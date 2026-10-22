import hmac
import json
import math
import os
import re
import secrets
import tempfile
import threading
import time
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone

import aprslib
from aprslib.exceptions import ConnectionError as APRSConnectionError, LoginError
from flask import (Flask, abort, flash, jsonify, request, redirect, render_template, session,
                   url_for)

import ax25
from i18n import LANGUAGES, _, get_language, js_translations
from symbols import SYMBOLS, SYMBOLS_BY_CODE, symbol_image

app = Flask(__name__)
APP_VERSION = os.environ.get("APP_VERSION", "dev")
CONFIG_FILE = os.environ.get("CONFIG_FILE", "config.json")
BEACONS_FILE = os.environ.get("BEACONS_FILE", "beacons.json")
DATA_DIR = os.path.dirname(os.path.abspath(CONFIG_FILE))
PASSWORD_FILE = os.environ.get("WEB_PASSWORD_FILE", os.path.join(DATA_DIR, "web_password.txt"))
SECRET_KEY_FILE = os.environ.get("SECRET_KEY_FILE", os.path.join(DATA_DIR, "secret_key.txt"))
WEB_USERNAME = os.environ.get("WEB_USERNAME", "admin")
SEND_INTERVAL = int(os.environ.get("SEND_INTERVAL", "300"))  # seconds between automatic transmissions
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))

LOGIN_MAX_FAILURES = 5    # failed logins per client ...
LOGIN_LOCK_SECONDS = 300  # ... before it has to wait this long

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)

# Guards every read-modify-write of the JSON files (web requests + sender thread).
data_lock = threading.RLock()

DEFAULT_CONFIG = {
    "callsign": "NOCALL",
    "passcode": "",
    "server": "euro.aprs2.net",
    "port": 14580,
    # Radio (RF) via a KISS TNC such as Direwolf
    "rf_enabled": False,
    "kiss_host": "",
    "kiss_port": 8001,
    "rf_path": "WIDE2-1",
    "rf_interval": 30,  # minutes
}

TOCALL = "APRS"  # destination address, identifies the sending software
CHANNELS = ("internet", "rf")
RF_INTERVAL_MIN = 10   # minutes; 144.800 MHz is a shared, slow channel
RF_INTERVAL_MAX = 120
RF_PATH_MAX = 2        # more hops only flood the network

CALLSIGN_RE = re.compile(r"^[A-Z0-9]{1,6}(-[A-Z0-9]{1,2})?$")
PASSCODE_RE = re.compile(r"^-?[0-9]{1,5}$")
HOST_RE = re.compile(r"^[A-Za-z0-9.-]{1,253}$")
OBJECT_NAME_MAX = 9
NAME_MAX = 50
TEXT_MAX = 100
TEXT_RECOMMENDED = 43  # APRS comment length most devices display

# Result of the last transmission per beacon id and channel (kept in memory):
# {beacon_id: {"internet": {"time": epoch, "ok": bool, "error": English message or None, "detail": str},
#              "rf": {...}}}
send_status = {}
send_status_lock = threading.Lock()
next_send = {"internet": 0.0, "rf": 0.0}  # time of the next automatic run per channel

# Status errors, translated when shown
ERR_INVALID_POSITION = "Invalid position"
ERR_LOGIN = "Login rejected – check callsign and passcode"
ERR_UNREACHABLE = "APRS-IS server not reachable"
ERR_SEND = "Sending failed"
ERR_TNC_UNREACHABLE = "TNC not reachable"
ERR_RF_CALLSIGN = "Callsign not usable on radio (SSID must be 0-15)"

# ==================== Helper functions ====================

def write_file_atomic(path, content):
    """Write to a temp file and rename, so readers never see a half-written file."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

def load_config():
    with data_lock:
        config = dict(DEFAULT_CONFIG)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config.update(json.load(f))
        return config

def save_config(config):
    with data_lock:
        write_file_atomic(CONFIG_FILE, json.dumps(config, indent=2))

def load_beacons():
    with data_lock:
        if not os.path.exists(BEACONS_FILE):
            return []
        with open(BEACONS_FILE, "r") as f:
            beacons = json.load(f)
        # Older files have no ids; assign stable ids once.
        if any("id" not in b for b in beacons):
            for b in beacons:
                b.setdefault("id", uuid.uuid4().hex)
            save_beacons(beacons)
        for b in beacons:
            b.setdefault("via", ["internet"])  # entries from before radio support
        return beacons

def save_beacons(beacons):
    with data_lock:
        write_file_atomic(BEACONS_FILE, json.dumps(beacons, indent=2))

def find_beacon(beacons, beacon_id):
    for idx, b in enumerate(beacons):
        if b.get("id") == beacon_id:
            return idx
    return None

def clean_text(value):
    """Remove control characters (CR/LF would split the APRS-IS line into extra packets)."""
    value = str(value or "")
    return "".join(c for c in value if not unicodedata.category(c).startswith("C")).strip()

def parse_position(value):
    """Return (lat, lon) as floats or raise ValueError."""
    parts = str(value or "").split(",")
    if len(parts) != 2:
        raise ValueError("Position must be 'lat,lon'")
    lat, lon = float(parts[0]), float(parts[1])
    if not (math.isfinite(lat) and math.isfinite(lon)):
        raise ValueError("Position must be a number")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Position out of range")
    return lat, lon

def is_valid_symbol(symbol):
    return (
        isinstance(symbol, str)
        and len(symbol) == 2
        and symbol[0] in "/\\"
        and 0x21 <= ord(symbol[1]) <= 0x7E
    )

def beacon_from_form(form, beacon_id=None):
    """Build a beacon dict from submitted form data. Returns (beacon, errors)."""
    errors = []
    beacon_type = form.get("type", "beacon")
    if beacon_type not in ("beacon", "object"):
        errors.append(_("Invalid type."))
        beacon_type = "beacon"

    name = clean_text(form.get("name"))
    if not name:
        errors.append(_("Name is required."))
    elif beacon_type == "object":
        if len(name) > OBJECT_NAME_MAX:
            errors.append(_("Object names may have at most {n} characters.", n=OBJECT_NAME_MAX))
        elif not all(0x20 <= ord(c) <= 0x7E for c in name):
            errors.append(_("Object names may only contain ASCII characters."))
    elif len(name) > NAME_MAX:
        errors.append(_("Name may have at most {n} characters.", n=NAME_MAX))

    text = clean_text(form.get("text"))
    if len(text) > TEXT_MAX:
        errors.append(_("Text may have at most {n} characters.", n=TEXT_MAX))

    position = form.get("position", "").strip()
    try:
        lat, lon = parse_position(position)
        position = f"{lat:.6f},{lon:.6f}"
    except ValueError:
        errors.append(_("Position must be 'latitude,longitude' in decimal degrees, e.g. 52.2450,8.9057."))

    symbol = form.get("symbol", "")
    if not is_valid_symbol(symbol):
        errors.append(_("Please choose a symbol."))

    via = [channel for channel in CHANNELS if channel in form.getlist("via")]
    if not via:
        errors.append(_("Choose at least one way to send: Internet or radio."))

    beacon = {
        "id": beacon_id or uuid.uuid4().hex,
        "name": name,
        "text": text,
        "position": position,
        "symbol": symbol,
        "type": beacon_type,
        "active": "active" in form,
        "via": via,
    }
    return beacon, errors

def config_from_form(form, current, include_rf=True):
    """Build the config from submitted form data. Returns (config, errors)."""
    errors = []
    callsign = form.get("callsign", "").strip().upper()
    if not CALLSIGN_RE.match(callsign):
        errors.append(_("Invalid callsign (e.g. DL8YDP or DL8YDP-9)."))
    # An empty passcode field keeps the stored passcode (it is never sent to the browser).
    passcode = form.get("passcode", "").strip() or str(current.get("passcode", ""))
    if not PASSCODE_RE.match(passcode):
        errors.append(_("Passcode must be a number."))
    server = form.get("server", "").strip()
    if not HOST_RE.match(server):
        errors.append(_("Invalid server name."))
    try:
        port = int(form.get("port", ""))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        errors.append(_("Port must be a number between 1 and 65535."))
        port = form.get("port", "")
    config = {"callsign": callsign, "passcode": passcode, "server": server, "port": port}
    if include_rf:
        config.update(rf_config_from_form(form, callsign, errors))
    return config, errors

def parse_rf_path(text):
    """'wide1-1, WIDE2-1' -> ['WIDE1-1', 'WIDE2-1']. Raises ValueError."""
    path = [p.strip().upper() for p in str(text or "").split(",") if p.strip()]
    if len(path) > RF_PATH_MAX or not all(ax25.is_valid_address(p) for p in path):
        raise ValueError("Invalid path")
    return path

def rf_config_from_form(form, callsign, errors):
    """Radio settings from the config form; appends messages to errors."""
    enabled = "rf_enabled" in form
    host = form.get("kiss_host", "").strip()
    if (enabled or host) and not HOST_RE.match(host):
        errors.append(_("Invalid TNC address."))
    try:
        kiss_port = int(form.get("kiss_port", "") or 8001)
        if not 1 <= kiss_port <= 65535:
            raise ValueError
    except ValueError:
        errors.append(_("TNC port must be a number between 1 and 65535."))
        kiss_port = form.get("kiss_port", "")
    try:
        path = ",".join(parse_rf_path(form.get("rf_path", "")))
    except ValueError:
        errors.append(_("Invalid path. Use up to {n} entries like WIDE1-1,WIDE2-1, or leave it empty.", n=RF_PATH_MAX))
        path = form.get("rf_path", "")
    try:
        interval = int(form.get("rf_interval", "") or 30)
        if not RF_INTERVAL_MIN <= interval <= RF_INTERVAL_MAX:
            raise ValueError
    except ValueError:
        errors.append(_("The radio interval must be between {min} and {max} minutes.",
                        min=RF_INTERVAL_MIN, max=RF_INTERVAL_MAX))
        interval = form.get("rf_interval", "")
    if enabled and CALLSIGN_RE.match(callsign) and not ax25.is_valid_address(callsign):
        errors.append(_("On radio the SSID must be a number from 0 to 15 (e.g. DL8YDP-10)."))
    return {"rf_enabled": enabled, "kiss_host": host, "kiss_port": kiss_port,
            "rf_path": path, "rf_interval": interval}

# ==================== Security ====================

_web_password = None

def get_web_password():
    """Password from WEB_PASSWORD, else from the password file, else generate one."""
    global _web_password
    if _web_password:
        return _web_password
    password = os.environ.get("WEB_PASSWORD", "")
    if not password and os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as f:
            password = f.read().strip()
        if password:
            print(f"Web login: user '{WEB_USERNAME}', password stored in {PASSWORD_FILE}", flush=True)
    if not password:
        password = secrets.token_urlsafe(12)
        write_file_atomic(PASSWORD_FILE, password + "\n")
        print(f"Generated web login: user '{WEB_USERNAME}', password '{password}' "
              f"(stored in {PASSWORD_FILE}, set WEB_PASSWORD to choose your own)", flush=True)
    _web_password = password
    return password

def load_secret_key():
    """Persist the session key, so logins survive a restart."""
    key = os.environ.get("SECRET_KEY", "")
    if not key and os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "r") as f:
            key = f.read().strip()
    if not key:
        key = secrets.token_hex(32)
        write_file_atomic(SECRET_KEY_FILE, key + "\n")
    return key

app.secret_key = load_secret_key()

def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]

# Failed logins per client address: {ip: (count, time of last failure)}
login_failures = {}
login_failures_lock = threading.Lock()

def login_locked(ip):
    with login_failures_lock:
        count, last = login_failures.get(ip, (0, 0))
        if count >= LOGIN_MAX_FAILURES and time.time() - last < LOGIN_LOCK_SECONDS:
            return True
        if count >= LOGIN_MAX_FAILURES:
            del login_failures[ip]
        return False

def record_login_failure(ip):
    with login_failures_lock:
        count, _unused = login_failures.get(ip, (0, 0))
        login_failures[ip] = (count + 1, time.time())

def check_credentials(username, password):
    user_ok = hmac.compare_digest(username.encode(), WEB_USERNAME.encode())
    password_ok = hmac.compare_digest(password.encode(), get_web_password().encode())
    return user_ok and password_ok

def safe_next_url(target):
    """Only allow redirects to local paths (no open redirect)."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return url_for("index")

PUBLIC_ENDPOINTS = ("static", "login", "set_language")

@app.before_request
def check_login_and_csrf():
    if request.endpoint == "static":
        return None
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not expected or not hmac.compare_digest(sent.encode(), expected.encode()):
            if request.endpoint == "login":
                flash(_("Your session expired. Please try again."), "warning")
                return redirect(url_for("login"))
            abort(400, "Invalid or expired form token. Please reload the page and try again.")
    if request.endpoint in PUBLIC_ENDPOINTS or session.get("user") == WEB_USERNAME:
        return None
    if request.path.startswith("/api/"):
        return jsonify({"error": "login required"}), 401
    return redirect(url_for("login", next=request.full_path if request.query_string else request.path))

@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response

# ==================== Template helpers ====================

def symbol_name(code):
    symbol = SYMBOLS_BY_CODE.get(code)
    return symbol["names"].get(get_language(), symbol["names"]["en"]) if symbol else code

def active_channels(beacon, config):
    """Channels this beacon is sent on right now (radio only while it is enabled)."""
    return [c for c in beacon.get("via", ["internet"]) if c != "rf" or config.get("rf_enabled")]

def status_for_client(beacon_id):
    """Last transmission per channel with translated error texts."""
    with send_status_lock:
        channels = {c: dict(s) for c, s in (send_status.get(beacon_id) or {}).items()}
    for status in channels.values():
        if status.get("error"):
            status["error"] = _(status["error"])
    return channels

@app.context_processor
def template_globals():
    return {
        "_": _,
        "csrf_token": csrf_token,
        "lang": get_language(),
        "languages": LANGUAGES,
        "js_i18n": js_translations(),
        "symbol_name": symbol_name,
        "symbol_image": symbol_image,
        "text_recommended": TEXT_RECOMMENDED,
        "text_max": TEXT_MAX,
        "object_name_max": OBJECT_NAME_MAX,
        "name_max": NAME_MAX,
        "send_interval": SEND_INTERVAL,
        "rf_interval_min": RF_INTERVAL_MIN,
        "rf_interval_max": RF_INTERVAL_MAX,
    }

# ==================== APRS-Sending ====================

def parse_symbol(beacon):
    """Parse symbol table and symbol character from beacon config."""
    symbol_input = beacon.get("symbol", "/>")
    if is_valid_symbol(symbol_input):
        return symbol_input[0], symbol_input[1]
    return '/', '>'

def format_position(lat, lon, symbol_table='/'):
    ns = 'N' if lat >= 0 else 'S'
    ew = 'E' if lon >= 0 else 'W'
    # Round to hundredths of a minute first, so 59.996' carries over to the next degree
    # instead of producing an invalid "60.00".
    lat_hmin = round(abs(lat) * 6000)
    lon_hmin = round(abs(lon) * 6000)
    lat_deg, lat_min = divmod(lat_hmin, 6000)
    lon_deg, lon_min = divmod(lon_hmin, 6000)
    return (f"{lat_deg:02d}{lat_min / 100:05.2f}{ns}{symbol_table}"
            f"{lon_deg:03d}{lon_min / 100:05.2f}{ew}")

def build_info(beacon, kill=False):
    """The APRS information field (everything after the ':'). Raises ValueError on bad data."""
    lat, lon = parse_position(beacon.get("position"))
    symbol_table, symbol = parse_symbol(beacon)
    pos = format_position(lat, lon, symbol_table)
    text = clean_text(beacon.get("text", ""))[:TEXT_MAX]
    if beacon.get("type", "beacon") == "object":
        objname = clean_text(beacon.get("name", ""))[:OBJECT_NAME_MAX].ljust(OBJECT_NAME_MAX)
        timestamp = datetime.now(timezone.utc).strftime("%d%H%Mz")
        state = "_" if kill else "*"
        return f";{objname}{state}{timestamp}{pos}{symbol}{text}"
    return f"={pos}{symbol}{text}"

def config_callsign(config):
    return clean_text(config["callsign"]).upper()

def build_packet(beacon, callsign, kill=False):
    """The APRS-IS line for a beacon or object. Raises ValueError on bad data."""
    return f"{callsign}>{TOCALL},TCPIP*:{build_info(beacon, kill=kill)}"

def rf_path(config):
    try:
        return parse_rf_path(config.get("rf_path", ""))
    except ValueError:
        return []

def rf_monitor_line(beacon, config):
    """The radio packet in the usual text form, as a TNC would show it."""
    return f"{config_callsign(config)}>{','.join([TOCALL] + rf_path(config))}:{build_info(beacon)}"

def aprs_connection(config):
    return aprslib.IS(
        config_callsign(config),
        passwd=str(config["passcode"]),
        host=config["server"],
        port=int(config["port"])
    )

def describe_error(exc):
    """Map an exception from aprslib to a short status message (English, translated later)."""
    if isinstance(exc, LoginError):
        return ERR_LOGIN
    if isinstance(exc, (APRSConnectionError, OSError)):
        return ERR_UNREACHABLE
    return ERR_SEND

def record_status(beacon_ids, channel, ok, error=None, detail=""):
    now = time.time()
    with send_status_lock:
        for beacon_id in beacon_ids:
            send_status.setdefault(beacon_id, {})[channel] = {
                "time": now, "ok": ok, "error": error, "detail": detail}

def prepare(beacons, build, channel, kill):
    """Build a packet per beacon; invalid ones get an error status. Returns [(id, packet)]."""
    packets = []
    for beacon in beacons:
        try:
            packets.append((beacon.get("id"), build(beacon)))
        except ValueError:
            print(f"Invalid position for '{beacon.get('name', '?')}': {beacon.get('position')}", flush=True)
            if not kill:
                record_status([beacon.get("id")], channel, False, ERR_INVALID_POSITION)
    return packets

def send_internet(beacons, config, kill=False):
    """Send several beacons over one APRS-IS connection. Returns True on success."""
    callsign = config_callsign(config)
    packets = prepare(beacons, lambda b: build_packet(b, callsign, kill=kill), "internet", kill)
    if not packets:
        return False

    conn = aprs_connection(config)
    try:
        conn.connect()
        for beacon_id, packet in packets:
            conn.sendall(packet)
            print(f"Sent: {packet}", flush=True)
            if not kill:
                record_status([beacon_id], "internet", True)
        return True
    except Exception as e:
        print(f"Error when sending to APRS-IS: {e}", flush=True)
        if not kill:
            record_status([beacon_id for beacon_id, _packet in packets], "internet", False, describe_error(e), str(e))
        return False
    finally:
        conn.close()

def send_rf(beacons, config, kill=False):
    """Hand beacons to the KISS TNC, which transmits them on air. Returns True on success."""
    callsign = config_callsign(config)
    ids = [b.get("id") for b in beacons]
    if not ax25.is_valid_address(callsign):
        if not kill:
            record_status(ids, "rf", False, ERR_RF_CALLSIGN)
        return False
    path = rf_path(config)
    frames = prepare(beacons, lambda b: ax25.encode_ui_frame(callsign, TOCALL, path, build_info(b, kill=kill)),
                     "rf", kill)
    if not frames:
        return False
    try:
        ax25.send_kiss_tcp(config["kiss_host"], config["kiss_port"], [frame for _id, frame in frames])
    except OSError as e:
        print(f"Error when sending to TNC {config['kiss_host']}:{config['kiss_port']}: {e}", flush=True)
        if not kill:
            record_status([beacon_id for beacon_id, _frame in frames], "rf", False, ERR_TNC_UNREACHABLE, str(e))
        return False
    for beacon_id, frame in frames:
        print(f"Sent on radio: {ax25.decode_ui_frame(frame)}", flush=True)
        if not kill:
            record_status([beacon_id], "rf", True)
    return True

SENDERS = {"internet": send_internet, "rf": send_rf}

def send_now(beacon, config):
    """Send one beacon on all its channels. Returns {channel: success}."""
    return {channel: SENDERS[channel]([beacon], config) for channel in active_channels(beacon, config)}

def send_kill_if_object(beacon, config):
    """Remove an object from the APRS maps instead of letting it time out."""
    if beacon.get("type") == "object" and beacon.get("active", True):
        for channel in active_channels(beacon, config):
            SENDERS[channel]([beacon], config, kill=True)

def channel_interval(channel, config):
    if channel == "rf":
        return int(config.get("rf_interval") or 30) * 60
    return SEND_INTERVAL

def run_due_channels():
    """Send every channel whose time has come. Called by the scheduler loop."""
    config = load_config()
    now = time.time()
    for channel in CHANNELS:
        if channel == "rf" and not config.get("rf_enabled"):
            next_send["rf"] = 0.0
            continue
        if now < next_send[channel]:
            continue
        next_send[channel] = now + channel_interval(channel, config)
        beacons = [b for b in load_beacons()
                   if b.get("active", True) and channel in active_channels(b, config)]
        if beacons:
            SENDERS[channel](beacons, config)

def auto_sender():
    while True:
        try:
            run_due_channels()
        except Exception as e:
            # Never let a bad file or network error stop the sender for good.
            print(f"Error in automatic sender: {e}", flush=True)
        time.sleep(5)

# ==================== Web-Gui ====================

@app.route("/lang/<code>")
def set_language(code):
    response = redirect(safe_next_url(request.args.get("next")))
    if code in LANGUAGES:
        response.set_cookie("lang", code, max_age=365 * 24 * 3600, samesite="Lax", httponly=True)
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = safe_next_url(request.values.get("next"))
    if session.get("user") == WEB_USERNAME:
        return redirect(next_url)

    if request.method == "POST":
        ip = request.remote_addr or "?"
        username = request.form.get("username", "")
        if login_locked(ip):
            flash(_("Too many failed attempts. Please wait {n} minutes.", n=LOGIN_LOCK_SECONDS // 60), "danger")
        elif check_credentials(username, request.form.get("password", "")):
            session.clear()  # new session after login (no session fixation)
            session["user"] = WEB_USERNAME
            session.permanent = "remember" in request.form
            return redirect(next_url)
        else:
            record_login_failure(ip)
            print(f"Failed login for '{username}' from {ip}", flush=True)
            flash(_("Wrong username or password."), "danger")
        return render_template("login.html", next=next_url, username=username), 401

    return render_template("login.html", next=next_url, username="")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash(_("You have been logged out."), "success")
    return redirect(url_for("login"))

@app.route("/")
def index():
    config = load_config()
    beacons = load_beacons()
    map_items = []
    for b in beacons:
        try:
            lat, lon = parse_position(b.get("position"))
        except ValueError:
            continue
        image = symbol_image(b.get("symbol"))
        map_items.append({
            "id": b["id"], "name": b.get("name", ""), "text": b.get("text", ""),
            "lat": lat, "lon": lon, "active": b.get("active", True),
            "icon": url_for("static", filename=f"symbols/{image}") if image else None,
        })
    statuses = {b["id"]: status_for_client(b["id"]) for b in beacons}
    channels = {b["id"]: active_channels(b, config) for b in beacons}
    return render_template("index.html", config=config, beacons=beacons, version=APP_VERSION,
                           map_items=map_items, statuses=statuses, channels=channels)

@app.route("/api/status")
def api_status():
    config = load_config()
    beacons = load_beacons()
    return jsonify({
        "now": time.time(),
        "next_send": {c: next_send[c] for c in CHANNELS if c != "rf" or config.get("rf_enabled")},
        "beacons": {b["id"]: status_for_client(b["id"]) for b in beacons},
        "channels": {b["id"]: active_channels(b, config) for b in beacons},
    })

@app.route("/api/preview")
def api_preview():
    """The packets the current form values would produce, per channel."""
    beacon = {
        "name": request.args.get("name", ""),
        "text": request.args.get("text", ""),
        "position": request.args.get("position", ""),
        "symbol": request.args.get("symbol", ""),
        "type": request.args.get("type", "beacon"),
    }
    if not is_valid_symbol(beacon["symbol"]):
        return jsonify({"error": _("Please choose a symbol.")})
    config = load_config()
    try:
        return jsonify({"internet": build_packet(beacon, config_callsign(config)),
                        "rf": rf_monitor_line(beacon, config)})
    except ValueError:
        return jsonify({"error": _("Enter a valid position or click on the map.")})

@app.route("/api/test-connection", methods=["POST"])
def api_test_connection():
    """Log in to APRS-IS with the values from the config form, without saving them."""
    cfg, errors = config_from_form(request.form, load_config(), include_rf=False)
    if errors:
        return jsonify({"ok": False, "message": " ".join(errors)})
    conn = aprs_connection(cfg)
    try:
        conn.connect()
        return jsonify({"ok": True, "message": _("Connected and logged in as {call} at {server}:{port}.",
                                                 call=cfg["callsign"], server=cfg["server"], port=cfg["port"])})
    except LoginError:
        return jsonify({"ok": False, "message": _("The server rejected the login. Check callsign and passcode.")})
    except Exception as e:
        print(f"Connection test failed: {e}", flush=True)
        return jsonify({"ok": False, "message": _("Could not connect to {server}:{port}.",
                                                  server=cfg["server"], port=cfg["port"])})
    finally:
        conn.close()

@app.route("/api/test-tnc", methods=["POST"])
def api_test_tnc():
    """Check that the TNC accepts connections. Nothing is transmitted."""
    host = request.form.get("kiss_host", "").strip()
    try:
        port = int(request.form.get("kiss_port", "") or 8001)
        if not HOST_RE.match(host) or not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        return jsonify({"ok": False, "message": _("Please enter the address and port of the TNC.")})
    try:
        ax25.check_kiss_tcp(host, port)
    except OSError as e:
        print(f"TNC test failed: {e}", flush=True)
        return jsonify({"ok": False, "message": _("Could not connect to the TNC at {host}:{port}. Is Direwolf running?",
                                                  host=host, port=port)})
    return jsonify({"ok": True, "message": _("The TNC at {host}:{port} accepts connections. Nothing was transmitted.",
                                             host=host, port=port)})

@app.route("/config", methods=["GET", "POST"])
def config_page():
    if request.method == "POST":
        with data_lock:
            current = load_config()
            cfg, errors = config_from_form(request.form, current)
            if errors:
                return render_template("config.html", config=cfg, errors=errors,
                                       has_passcode=bool(current.get("passcode"))), 400
            save_config(cfg)
        flash(_("Configuration saved."), "success")
        return redirect(url_for("index"))

    config = load_config()
    return render_template("config.html", config=config, has_passcode=bool(config.get("passcode")))

def form_context():
    return {"symbols": SYMBOLS, "rf_enabled": load_config().get("rf_enabled", False)}

@app.route("/new", methods=["GET", "POST"])
def new_beacon():
    if request.method == "POST":
        beacon, errors = beacon_from_form(request.form)
        if errors:
            return render_template("new.html", beacon=beacon, errors=errors, **form_context()), 400
        with data_lock:
            beacons = load_beacons()
            beacons.append(beacon)
            save_beacons(beacons)
        flash(_("'{name}' created.", name=beacon["name"]), "success")
        return redirect(url_for("index"))
    return render_template("new.html", beacon={"active": True, "type": "beacon", "via": ["internet"]},
                           **form_context())

@app.route("/toggle/<beacon_id>", methods=["POST"])
def toggle_beacon(beacon_id):
    with data_lock:
        beacons = load_beacons()
        idx = find_beacon(beacons, beacon_id)
        if idx is None:
            abort(404)
        beacon = dict(beacons[idx])
        beacons[idx]["active"] = not beacon.get("active", True)
        save_beacons(beacons)
    if not beacons[idx]["active"]:
        send_kill_if_object(beacon, load_config())
    return redirect(url_for("index"))

@app.route("/send/<beacon_id>", methods=["POST"])
def send_once(beacon_id):
    beacons = load_beacons()
    idx = find_beacon(beacons, beacon_id)
    if idx is None:
        abort(404)
    name = beacons[idx]["name"]
    results = send_now(beacons[idx], load_config())
    statuses = status_for_client(beacon_id)
    labels = {"internet": _("Internet"), "rf": _("Radio")}
    for channel, ok in results.items():
        if ok:
            flash(_("'{name}' sent ({channel}).", name=name, channel=labels[channel]), "success")
        else:
            flash(_("Sending '{name}' failed ({channel}): {error}", name=name, channel=labels[channel],
                    error=statuses.get(channel, {}).get("error", "")), "danger")
    if not results:
        flash(_("'{name}' has no active way to send. Radio is switched off in the configuration.", name=name),
              "warning")
    return redirect(url_for("index"))

@app.route("/edit/<beacon_id>", methods=["GET", "POST"])
def edit_beacon(beacon_id):
    beacons = load_beacons()
    idx = find_beacon(beacons, beacon_id)
    if idx is None:
        return redirect(url_for("index"))

    if request.method == "POST":
        beacon, errors = beacon_from_form(request.form, beacon_id=beacon_id)
        if errors:
            return render_template("edit.html", beacon=beacon, errors=errors, **form_context()), 400
        with data_lock:
            beacons = load_beacons()
            idx = find_beacon(beacons, beacon_id)
            if idx is None:
                abort(404)
            beacons[idx] = beacon
            save_beacons(beacons)
        flash(_("'{name}' saved.", name=beacon["name"]), "success")
        return redirect(url_for("index"))

    return render_template("edit.html", beacon=beacons[idx], **form_context())

@app.route("/delete/<beacon_id>", methods=["POST"])
def delete_beacon(beacon_id):
    with data_lock:
        beacons = load_beacons()
        idx = find_beacon(beacons, beacon_id)
        if idx is None:
            abort(404)
        beacon = beacons.pop(idx)
        save_beacons(beacons)
    with send_status_lock:
        send_status.pop(beacon_id, None)
    send_kill_if_object(beacon, load_config())
    flash(_("'{name}' deleted.", name=beacon["name"]), "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    from waitress import serve

    get_web_password()
    threading.Thread(target=auto_sender, daemon=True).start()
    serve(app, host=HOST, port=PORT)
