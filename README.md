# lightAPRSinjector - a lightweight APRS Beacon and Object Manager by DL8YDP

A lightweight Flask web application to manage and send APRS position beacons and objects via APRS-IS. Designed for amateur radio operators, it offers a modern and simple (Bootstrap) web interface to add, edit, activate, and send APRS data using configurable symbols (e.g., `/E` or `\E`), coordinates, and texts.

<img width="976" height="475" alt="Bildschirmfoto 2025-08-01 um 11 55 50" src="https://github.com/user-attachments/assets/737dfff7-fae9-4475-9c8b-cc628c6e0e15" />

## ✨ Features

- Send APRS position beacons or objects over APRS-IS  
- Symbol support using `/` and `\` tables (e.g., `/E` = Eyeball, `\E` = Smokestack)  
- Web interface for configuration and beacon management, in English and German  
- Overview map, live send status and countdown to the next transmission  
- Symbol picker with search, character counter and live packet preview  
- Supports manual and scheduled transmissions (every 5 minutes)  
- Built with Flask, `aprslib` and Bootstrap.

---

## 🚀 Installation

There are three ways to run lightAPRSinjector. Choose whichever fits best.

---

### Option 1: Docker (recommended)

The easiest way to get started. No Python setup or cloning required — the image is pulled directly from the GitHub Container Registry.

**1. Download the compose file**
```bash
curl -O https://raw.githubusercontent.com/HochdruckHummer/lightAPRSinjector/main/docker-compose.yml
```

**2. Start the container**
```bash
docker compose up -d
```

**3. Open in browser**

http://localhost:5000

Log in with user `admin` and the password shown in the container log on first start:
```bash
docker compose logs lightaprsinjektor | grep "web login"
```
See [Web login](#-web-login) to choose your own password.

Config and beacon data are stored in a persistent Docker volume (`aprs_data`), so your settings survive container restarts and updates.

**To update to the latest version:**
```bash
docker compose pull
docker compose up -d
```

---

### Option 2: Portainer (Docker with GUI)

If you manage your containers via Portainer (e.g. on a Raspberry Pi or home server), there are two ways — no manual cloning required.

#### 2a – Via Git repository (recommended)

Portainer can pull and build directly from GitHub, no terminal needed.

1. In Portainer: **Stacks → Add Stack → Repository**
2. Set the repository URL to:
   ```
   https://github.com/HochdruckHummer/lightAPRSinjector.git
   ```
3. Leave the branch as `main` and the compose path as `docker-compose.yml`
4. Click **Deploy the stack**

To update later: open the stack in Portainer and click **Pull and redeploy**.

#### 2b – Via Web Editor (copy & paste)

1. In Portainer: **Stacks → Add Stack → Web editor**
2. Paste the contents of the [`docker-compose.yml`](docker-compose.yml) from this repository
3. Click **Deploy the stack**

> **Note:** The image is pulled from `ghcr.io/hochdruckhummer/lightaprsinjektor:latest` — no build step needed. Both options work without cloning the repository.

The app will be available at `http://<your-server-ip>:5000`.

---

### Option 3: Manual (Python)

**1. Clone the repository**
```bash
git clone https://github.com/HochdruckHummer/lightAPRSinjector.git
cd lightAPRSinjector
```

**2. Create a virtual environment (recommended)**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Start the app**
```bash
python app.py
```

Open in browser: http://localhost:5000

---

## 🔒 Web login

The web interface is protected by a login page, because anyone who can open it can send APRS packets under your callsign. After 5 failed attempts a client has to wait 5 minutes.

- Username: `admin` (change with the environment variable `WEB_USERNAME`)
- Password: set it with the environment variable `WEB_PASSWORD`. If it is not set, a random password is generated on first start, printed to the log and stored in `web_password.txt` next to `config.json` (in Docker: `/data/web_password.txt`).
- "Stay logged in" keeps you logged in for 30 days, also across restarts (the session key is stored in `secret_key.txt`).

Over plain HTTP the password is sent unencrypted. If the app is reachable from outside your home network, put it behind a reverse proxy with HTTPS (e.g. Caddy, Traefik, nginx).

---

## ⚙️ Configuration

On first launch, open the web interface and set your callsign, APRS-IS passcode, server and port via the **Configuration** page.

Alternatively, create a `config.json` manually in the same directory as `app.py`:

```json
{
  "callsign": "DL8YDP",
  "passcode": "12345",
  "server": "euro.aprs2.net",
  "port": 14580
}
```

| Field | Description |
|---|---|
| `callsign` | Your full APRS callsign (e.g. `DL8YDP` or `DL8YDP-9`) |
| `passcode` | Your APRS-IS passcode – generate it [here](https://apps.magicbug.co.uk/passcode/) |
| `server` | APRS-IS server, e.g. `euro.aprs2.net` |
| `port` | Default: `14580` |

If `beacons.json` does not exist, it will be created automatically when adding your first beacon. Both files are listed in `.gitignore`, so your passcode does not end up in a commit.

---

## 🖥️ Usage

### Web Interface Features

<img width="691" height="786" alt="Screenshot_new_APRS_beacon_or_object" src="https://github.com/user-attachments/assets/21b5d3ce-31ef-40ef-b545-b5bb2ff26d9a" />

- **Overview:** all entries on a map and in a list with status (active/inactive), the result of the last transmission and a countdown to the next automatic run
- **Edit config:** Set callsign, passcode, server and port, and check them with **Test connection**
- **Add beacon or object:**
  - Type: beacon (your own position) or object (a marker with its own name)
  - Name: max 9 characters for APRS objects
  - Position: latitude and longitude separated by comma (e.g. `52.2450,8.9057`) or selected on the map
  - Symbol: pick from about 170 APRS symbols, searchable by name in English and German
  - Text: description with a character counter (max 43 characters recommended)
  - Packet preview: shows exactly what will be sent
- **Toggle Active:** Enable/disable specific entries with the switch
- **Send Now:** Immediately transmit a beacon or object
- **Edit/Delete:** Modify or remove existing entries (in the ⋯ menu)
- **Language:** switch between English and German with the EN/DE buttons in the header

---

## 🔁 Auto Transmission

A background thread automatically transmits all active entries every 5 minutes.

To change the interval, set the environment variable `SEND_INTERVAL` (in seconds), e.g. `SEND_INTERVAL=600`. For fixed stations and objects, 10–30 minutes is the usual courtesy on APRS-IS.

When an active object is deactivated or deleted, a kill packet is sent so it disappears from maps like aprs.fi right away.

---

## 🛠️ Notes

- APRS object names are limited to 9 characters
- Symbol codes consist of two characters: `/` or `\` plus the actual symbol (e.g. `/E`)
- The first character determines the symbol table; the second is the symbol itself

---

## Support the development

Did this application help you?  
If you like, you can send me a beer via PayPal:

<a href="https://paypal.me/DanielBeckemeier" target="_blank" rel="nofollow sponsored noopener">
  <img
    width="300"
    height="50"
    alt="Donate a beer"
    src="https://github.com/user-attachments/assets/7c223db3-f267-447e-9207-4fe1cc72f829"
  />
</a>

---

## 📜 License

This project is licensed under the MIT License.

## 📡 Author

Created by DL8YDP  
Pull requests and contributions are welcome!
