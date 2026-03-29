import json
import time
import threading
from flask import Flask, request, redirect, url_for, render_template

import aprslib
import os
from datetime import datetime

app = Flask(__name__)
CONFIG_FILE = os.environ.get("CONFIG_FILE", "config.json")
BEACONS_FILE = os.environ.get("BEACONS_FILE", "beacons.json")
SEND_INTERVAL = 300  # send all 5 minutes

# ==================== Helper functions ====================

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "callsign": "NOCALL",
            "passcode": "",
            "server": "euro.aprs2.net",
            "port": 14580
        }
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def load_beacons():
    if not os.path.exists(BEACONS_FILE):
        return []
    with open(BEACONS_FILE, "r") as f:
        return json.load(f)

def save_beacons(beacons):
    with open(BEACONS_FILE, "w") as f:
        json.dump(beacons, f, indent=2)

@app.route("/new", methods=["GET", "POST"])
def new_beacon():
    if request.method == "POST":
        beacons = load_beacons()
        new_beacon = {
            "name": request.form["name"],
            "text": request.form["text"],
            "position": request.form["position"],
            "symbol": request.form["symbol"],
            "type": request.form.get("type", "beacon"),
            "active": "active" in request.form
        }
        beacons.append(new_beacon)
        save_beacons(beacons)
        return redirect(url_for("index"))
    return render_template("new.html")

# ==================== APRS-Sending ====================

def parse_symbol(beacon):
    """Parse symbol table and symbol character from beacon config."""
    symbol_input = beacon.get("symbol", "/>")
    if len(symbol_input) == 2:
        return symbol_input[0], symbol_input[1]
    return '/', '>'

def get_aprs_connection(config):
    """Create and return a connected APRS-IS connection."""
    conn = aprslib.IS(
        config["callsign"],
        passwd=config["passcode"],
        host=config["server"],
        port=int(config["port"])  # FIX #3: always cast port to int
    )
    conn.connect()
    return conn

def send_position_beacon(beacon, config):
    # FIX #2: validate position before sending
    try:
        lat, lon = map(float, beacon["position"].split(","))
    except (ValueError, AttributeError):
        print(f"Ungültige Position für Beacon '{beacon.get('name', '?')}': {beacon.get('position')}")
        return

    try:
        conn = get_aprs_connection(config)
        symbol_table, symbol = parse_symbol(beacon)
        pos = format_position(lat, lon, symbol_table)
        conn.sendall(f"{config['callsign']}>APRS,TCPIP*:={pos}{symbol}{beacon.get('text','')}")
        conn.close()
        print(f"Gesendet: {beacon['text']}")
    except Exception as e:
        print(f"Error when sending the beacon: {e}")

def send_object(beacon, config):
    # FIX #2: validate position before sending
    try:
        lat, lon = map(float, beacon["position"].split(","))
    except (ValueError, AttributeError):
        print(f"Ungültige Position für Objekt '{beacon.get('name', '?')}': {beacon.get('position')}")
        return

    try:
        conn = get_aprs_connection(config)
        symbol_table, symbol = parse_symbol(beacon)
        pos = format_position(lat, lon, symbol_table)
        timestamp = datetime.utcnow().strftime("%d%H%Mz")
        objname = beacon['name'][:9].ljust(9)
        text = beacon.get('text', '')
        packet = f";{objname}*{timestamp}{pos}{symbol}{text}"
        conn.sendall(f"{config['callsign']}>APRS,TCPIP*:{packet}")
        conn.close()
        print(f"Objekt gesendet: {objname.strip()} ({pos})")
    except Exception as e:
        print(f"Fehler beim Senden des Objekts: {e}")


def send_beacon(beacon, config):
    if beacon.get("type", "beacon") == "object":
        send_object(beacon, config)
    else:
        send_position_beacon(beacon, config)

def format_position(lat, lon, symbol_table='/'):
    ns = 'N' if lat >= 0 else 'S'
    ew = 'E' if lon >= 0 else 'W'
    lat = abs(lat)
    lon = abs(lon)
    lat_deg = int(lat)
    lat_min = (lat - lat_deg) * 60
    lon_deg = int(lon)
    lon_min = (lon - lon_deg) * 60
    return f"{lat_deg:02d}{lat_min:05.2f}{ns}{symbol_table}{lon_deg:03d}{lon_min:05.2f}{ew}"

def auto_sender():
    while True:
        config = load_config()
        beacons = load_beacons()
        for beacon in beacons:
            if beacon.get("active", True):
                send_beacon(beacon, config)
        time.sleep(SEND_INTERVAL)

threading.Thread(target=auto_sender, daemon=True).start()

# ==================== Web-Gui ====================

@app.route("/")
def index():
    config = load_config()
    beacons = load_beacons()
    return render_template("index.html", config=config, beacons=beacons)

@app.route("/config", methods=["GET", "POST"])
def config_page():
    if request.method == "POST":
        cfg = {
            "callsign": request.form["callsign"],
            "passcode": request.form["passcode"],
            "server": request.form["server"],
            "port": int(request.form["port"]),
        }
        save_config(cfg)
        return redirect(url_for("index"))

    config = load_config()
    return render_template("config.html", config=config)

@app.route("/add", methods=["POST"])
def add_beacon():
    beacons = load_beacons()
    new_beacon = {
        "name": request.form["name"],
        "text": request.form["text"],
        "position": request.form["position"],
        "symbol": request.form["symbol"],
        "type": request.form.get("type", "beacon"),
        "active": "active" in request.form
    }
    beacons.append(new_beacon)
    save_beacons(beacons)
    return redirect(url_for("index"))

@app.route("/toggle/<int:idx>", methods=["POST"])
def toggle_beacon(idx):
    beacons = load_beacons()
    if 0 <= idx < len(beacons):
        beacons[idx]["active"] = not beacons[idx].get("active", True)
    save_beacons(beacons)
    return redirect(url_for("index"))

@app.route("/send/<int:idx>", methods=["POST"])
def send_once(idx):
    config = load_config()
    beacons = load_beacons()
    if 0 <= idx < len(beacons):
        send_beacon(beacons[idx], config)
    return redirect(url_for("index"))

@app.route("/edit/<int:idx>", methods=["GET", "POST"])
def edit_beacon(idx):
    beacons = load_beacons()
    if not (0 <= idx < len(beacons)):
        return redirect(url_for("index"))

    if request.method == "POST":
        beacons[idx] = {
            "name": request.form["name"],
            "text": request.form["text"],
            "position": request.form["position"],
            "symbol": request.form["symbol"],
            "type": request.form.get("type", "beacon"),
            "active": "active" in request.form
        }
        save_beacons(beacons)
        return redirect(url_for("index"))

    return render_template("edit.html", beacon=beacons[idx], index=idx)

@app.route("/delete/<int:idx>", methods=["POST"])
def delete_beacon(idx):
    beacons = load_beacons()
    if 0 <= idx < len(beacons):
        del beacons[idx]
        save_beacons(beacons)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
