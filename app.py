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
from datetime import datetime, timezone

import aprslib
from flask import Flask, Response, abort, flash, request, redirect, render_template, session, url_for

app = Flask(__name__)
APP_VERSION = os.environ.get("APP_VERSION", "dev")
CONFIG_FILE = os.environ.get("CONFIG_FILE", "config.json")
BEACONS_FILE = os.environ.get("BEACONS_FILE", "beacons.json")
DATA_DIR = os.path.dirname(os.path.abspath(CONFIG_FILE))
PASSWORD_FILE = os.environ.get("WEB_PASSWORD_FILE", os.path.join(DATA_DIR, "web_password.txt"))
WEB_USERNAME = os.environ.get("WEB_USERNAME", "admin")
SEND_INTERVAL = int(os.environ.get("SEND_INTERVAL", "300"))  # seconds between automatic transmissions
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))

# Session only holds the CSRF token, so a fresh key per process is fine.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict")

# Guards every read-modify-write of the JSON files (web requests + sender thread).
data_lock = threading.RLock()

DEFAULT_CONFIG = {
    "callsign": "NOCALL",
    "passcode": "",
    "server": "euro.aprs2.net",
    "port": 14580,
}

CALLSIGN_RE = re.compile(r"^[A-Z0-9]{1,6}(-[A-Z0-9]{1,2})?$")
PASSCODE_RE = re.compile(r"^-?[0-9]{1,5}$")
HOST_RE = re.compile(r"^[A-Za-z0-9.-]{1,253}$")
OBJECT_NAME_MAX = 9
NAME_MAX = 50
TEXT_MAX = 100

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
        errors.append("Invalid type.")
        beacon_type = "beacon"

    name = clean_text(form.get("name"))
    if not name:
        errors.append("Name is required.")
    elif beacon_type == "object":
        if len(name) > OBJECT_NAME_MAX:
            errors.append(f"Object names may have at most {OBJECT_NAME_MAX} characters.")
        elif not all(0x20 <= ord(c) <= 0x7E for c in name):
            errors.append("Object names may only contain ASCII characters.")
    elif len(name) > NAME_MAX:
        errors.append(f"Name may have at most {NAME_MAX} characters.")

    text = clean_text(form.get("text"))
    if len(text) > TEXT_MAX:
        errors.append(f"Text may have at most {TEXT_MAX} characters.")

    position = form.get("position", "").strip()
    try:
        lat, lon = parse_position(position)
        position = f"{lat:.6f},{lon:.6f}"
    except ValueError:
        errors.append("Position must be 'latitude,longitude' in decimal degrees, e.g. 52.2450,8.9057.")

    symbol = form.get("symbol", "")
    if not is_valid_symbol(symbol):
        errors.append("Please choose a symbol.")

    beacon = {
        "id": beacon_id or uuid.uuid4().hex,
        "name": name,
        "text": text,
        "position": position,
        "symbol": symbol,
        "type": beacon_type,
        "active": "active" in form,
    }
    return beacon, errors

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

def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]

app.jinja_env.globals["csrf_token"] = csrf_token

@app.before_request
def check_auth_and_csrf():
    if request.endpoint == "static":
        return None
    auth = request.authorization
    valid = (
        auth is not None
        and auth.type == "basic"
        and hmac.compare_digest((auth.username or "").encode(), WEB_USERNAME.encode())
        and hmac.compare_digest((auth.password or "").encode(), get_web_password().encode())
    )
    if not valid:
        return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="lightAPRSinjector"'})
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not expected or not hmac.compare_digest(sent.encode(), expected.encode()):
            abort(400, "Invalid or expired form token. Please reload the page and try again.")
    return None

@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response

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

def build_packet(beacon, callsign, kill=False):
    """Build the APRS-IS line for a beacon or object. Raises ValueError on bad data."""
    lat, lon = parse_position(beacon.get("position"))
    symbol_table, symbol = parse_symbol(beacon)
    pos = format_position(lat, lon, symbol_table)
    text = clean_text(beacon.get("text", ""))[:TEXT_MAX]
    if beacon.get("type", "beacon") == "object":
        objname = clean_text(beacon.get("name", ""))[:OBJECT_NAME_MAX].ljust(OBJECT_NAME_MAX)
        timestamp = datetime.now(timezone.utc).strftime("%d%H%Mz")
        state = "_" if kill else "*"
        body = f";{objname}{state}{timestamp}{pos}{symbol}{text}"
    else:
        body = f"={pos}{symbol}{text}"
    return f"{callsign}>APRS,TCPIP*:{body}"

def send_beacons(beacons, config, kill=False):
    """Send several beacons over one APRS-IS connection. Returns True on success."""
    callsign = clean_text(config["callsign"]).upper()
    packets = []
    for beacon in beacons:
        try:
            packets.append(build_packet(beacon, callsign, kill=kill))
        except ValueError:
            print(f"Invalid position for '{beacon.get('name', '?')}': {beacon.get('position')}", flush=True)
    if not packets:
        return False

    conn = aprslib.IS(
        callsign,
        passwd=str(config["passcode"]),
        host=config["server"],
        port=int(config["port"])
    )
    try:
        conn.connect()
        for packet in packets:
            conn.sendall(packet)
            print(f"Sent: {packet}", flush=True)
        return True
    except Exception as e:
        print(f"Error when sending to APRS-IS: {e}", flush=True)
        return False
    finally:
        conn.close()

def send_kill_if_object(beacon, config):
    """Remove an object from the APRS maps instead of letting it time out."""
    if beacon.get("type") == "object" and beacon.get("active", True):
        send_beacons([beacon], config, kill=True)

def auto_sender():
    while True:
        try:
            config = load_config()
            active = [b for b in load_beacons() if b.get("active", True)]
            send_beacons(active, config)
        except Exception as e:
            # Never let a bad file or network error stop the sender for good.
            print(f"Error in automatic sender: {e}", flush=True)
        time.sleep(SEND_INTERVAL)

# ==================== Web-Gui ====================

@app.route("/")
def index():
    config = load_config()
    beacons = load_beacons()
    return render_template("index.html", config=config, beacons=beacons, version=APP_VERSION)

@app.route("/config", methods=["GET", "POST"])
def config_page():
    if request.method == "POST":
        with data_lock:
            current = load_config()
            errors = []
            callsign = request.form.get("callsign", "").strip().upper()
            if not CALLSIGN_RE.match(callsign):
                errors.append("Invalid callsign (e.g. DL8YDP or DL8YDP-9).")
            # An empty passcode field keeps the stored passcode (it is never sent to the browser).
            passcode = request.form.get("passcode", "").strip() or str(current.get("passcode", ""))
            if not PASSCODE_RE.match(passcode):
                errors.append("Passcode must be a number.")
            server = request.form.get("server", "").strip()
            if not HOST_RE.match(server):
                errors.append("Invalid server name.")
            try:
                port = int(request.form.get("port", ""))
                if not 1 <= port <= 65535:
                    raise ValueError
            except ValueError:
                errors.append("Port must be a number between 1 and 65535.")
                port = request.form.get("port", "")

            cfg = {"callsign": callsign, "passcode": passcode, "server": server, "port": port}
            if errors:
                return render_template("config.html", config=cfg, errors=errors,
                                       has_passcode=bool(current.get("passcode"))), 400
            save_config(cfg)
        flash("Configuration saved.", "success")
        return redirect(url_for("index"))

    config = load_config()
    return render_template("config.html", config=config, has_passcode=bool(config.get("passcode")))

@app.route("/new", methods=["GET", "POST"])
def new_beacon():
    if request.method == "POST":
        beacon, errors = beacon_from_form(request.form)
        if errors:
            return render_template("new.html", beacon=beacon, errors=errors), 400
        with data_lock:
            beacons = load_beacons()
            beacons.append(beacon)
            save_beacons(beacons)
        return redirect(url_for("index"))
    return render_template("new.html", beacon={"active": True})

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
    if send_beacons([beacons[idx]], load_config()):
        flash(f"'{beacons[idx]['name']}' sent.", "success")
    else:
        flash(f"Sending '{beacons[idx]['name']}' failed, see log.", "danger")
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
            return render_template("edit.html", beacon=beacon, errors=errors), 400
        with data_lock:
            beacons = load_beacons()
            idx = find_beacon(beacons, beacon_id)
            if idx is None:
                abort(404)
            beacons[idx] = beacon
            save_beacons(beacons)
        return redirect(url_for("index"))

    return render_template("edit.html", beacon=beacons[idx])

@app.route("/delete/<beacon_id>", methods=["POST"])
def delete_beacon(beacon_id):
    with data_lock:
        beacons = load_beacons()
        idx = find_beacon(beacons, beacon_id)
        if idx is None:
            abort(404)
        beacon = beacons.pop(idx)
        save_beacons(beacons)
    send_kill_if_object(beacon, load_config())
    return redirect(url_for("index"))

if __name__ == "__main__":
    from waitress import serve

    get_web_password()
    threading.Thread(target=auto_sender, daemon=True).start()
    serve(app, host=HOST, port=PORT)
