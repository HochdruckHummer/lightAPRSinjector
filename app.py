import json
import time
import threading
from flask import Flask, request, redirect, url_for, render_template_string
import aprslib
import os
from datetime import datetime

app = Flask(__name__)
CONFIG_FILE = "config.json"
BEACONS_FILE = "beacons.json"
SEND_INTERVAL = 300  # send all 5 minutes

# ==================== Helpers ====================

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

# ==================== Sending APRS ====================

def send_position_beacon(beacon, config):
    try:
        conn = aprslib.IS(
            config["callsign"],
            passwd=config["passcode"],
            host=config["server"],
            port=config["port"]
        )
        conn.connect()
        lat, lon = map(float, beacon["position"].split(","))

        symbol_input = beacon.get("symbol", "/>")  # Default: "/>"
        if len(symbol_input) == 2:
            symbol_table = symbol_input[0]
            symbol = symbol_input[1]
        else:
            symbol_table = '/'
            symbol = '>'

        pos = format_position(lat, lon, symbol_table)
        conn.sendall(f"{config['callsign']}>APRS,TCPIP*:={pos}{symbol}{beacon.get('text','')}")
        conn.close()
        print(f"Gesendet: {beacon['text']}")
    except Exception as e:
        print(f"Fehler beim Senden der Bake: {e}")

def send_object(beacon, config):
    try:
        conn = aprslib.IS(
            config["callsign"],
            passwd=config["passcode"],
            host=config["server"],
            port=config["port"]
        )
        conn.connect()

        lat, lon = map(float, beacon["position"].split(","))

        symbol_input = beacon.get("symbol", "/>")  # Default: "/>"
        if len(symbol_input) == 2:
            symbol_table = symbol_input[0]
            symbol = symbol_input[1]
        else:
            symbol_table = '/'
            symbol = '>'

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
        send_object(beacon, config)  # If type "object", then send APRS-object
    else:
        send_position_beacon(beacon, config)  # Send normal beacon otherwise

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

# ==================== Web-Frontend ====================

HTML = """
<!doctype html>
<title>lightAPRSinjector</title>
<h1>APRS Beacon and Object Manager by DL8YDP</h1>

<h2>Configuration</h2>
<form method="post" action="/config">
  Rufzeichen: <input name="callsign" value="{{ config.callsign }}"><br>
  Passcode: <input name="passcode" value="{{ config.passcode }}"><br>
  Server: <input name="server" value="{{ config.server }}"><br>
  Port: <input name="port" value="{{ config.port }}"><br>
  <input type="submit" value="Save">
</form>

<h2>Add new APRS beacon or object</h2>
<form method="post" action="/add">
  Name: <input name="name"><br>
  Text: <input name="text"><br>
  Position (Lat,Lon): <input name="position"><br>
  Symbol: <input name="symbol" value="/"><br>
Typ:
<select name="type">
  <option value="beacon" selected>Position-Bake</option>
  <option value="object">APRS-Objekt</option>
</select><br>
Aktiv: <input type="checkbox" name="active" checked><br>
  <input type="submit" value="Add">
</form>

<h2>Active items</h2>
<ul>
{% for b in beacons %}
  <li>
    <b>{{ b.name }}</b>: {{ b.text }} ({{ b.position }}) [Symbol: {{ b.symbol }}]
    <i>({{ "Object" if b.type == "object" else "Beacon" }})</i>
    <form style="display:inline" method="post" action="/toggle/{{ loop.index0 }}">
      <button type="submit">{{ "Deactivate" if b.active else "Activate" }}</button>
    </form>
    <form style="display:inline" method="post" action="/send/{{ loop.index0 }}">
      <button type="submit">Send now</button>
    </form>
    <a href="{{ url_for('edit_beacon', idx=loop.index0) }}">Edit</a>
    <form style="display:inline" method="post" action="/delete/{{ loop.index0 }}" onsubmit="return confirm('Do you really really want to delete this beacon?');">
      <button type="submit">Delete</button>
    </form>
  </li>
{% endfor %}
</ul>
"""

EDIT_HTML = """
<!doctype html>
<title>Edit APRS item</title>
<h1>Edit APRS item</h1>

<form method="post" action="/edit/{{ index }}">
  Name: <input name="name" value="{{ beacon.name }}"><br>
  Text: <input name="text" value="{{ beacon.text }}"><br>
  Position (Lat,Lon): <input name="position" value="{{ beacon.position }}"><br>
  Symbol: <input name="symbol" value="{{ beacon.symbol }}"><br>
  Typ:
  <select name="type">
    <option value="beacon" {% if beacon.type == 'beacon' %}selected{% endif %}>Position-Bake</option>
    <option value="object" {% if beacon.type == 'object' %}selected{% endif %}>APRS-Objekt</option>
  </select><br>
  Aktiv: <input type="checkbox" name="active" {% if beacon.active %}checked{% endif %}><br>
  <input type="submit" value="Save">
</form>

<a href="/">Back</a>
"""


@app.route("/")
def index():
    config = load_config()
    beacons = load_beacons()
    return render_template_string(HTML, config=config, beacons=beacons)

@app.route("/config", methods=["POST"])
def update_config():
    cfg = {
        "callsign": request.form["callsign"],
        "passcode": request.form["passcode"],
        "server": request.form["server"],
        "port": int(request.form["port"]),
    }
    save_config(cfg)
    return redirect(url_for("index"))

@app.route("/add", methods=["POST"])
def add_beacon():
    beacons = load_beacons()
    new_beacon = {
    "name": request.form["name"],
    "text": request.form["text"],
    "position": request.form["position"],
    "symbol": request.form["symbol"],
    "type": request.form.get("type", "beacon"),  # new
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


# New route for editing (GET and POST)
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

    # GET: Formular mit vorhandenen Daten vorbefüllen und EDIT_HTML nutzen
    return render_template_string(EDIT_HTML, beacon=beacons[idx], index=idx)

# New route for deleting beacons
@app.route("/delete/<int:idx>", methods=["POST"])
def delete_beacon(idx):
    beacons = load_beacons()
    if 0 <= idx < len(beacons):
        del beacons[idx]
        save_beacons(beacons)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
