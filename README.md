# lightAPRSinjector - a lightweight APRS Beacon and Object Manager by DL8YDP

A lightweight Flask web application to manage and send APRS position beacons and objects via APRS-IS. Designed for amateur radio operators, it offers a modern and simple (Bootstrap) web interface to add, edit, activate, and send APRS data using configurable symbols (e.g., `/E` or `\E`), coordinates, and texts.

<img width="976" height="475" alt="Bildschirmfoto 2025-08-01 um 11 55 50" src="https://github.com/user-attachments/assets/737dfff7-fae9-4475-9c8b-cc628c6e0e15" />

## ✨ Features

- Send APRS position beacons or objects over APRS-IS  
- Symbol support using `/` and `\` tables (e.g., `/E` = Eyeball, `\E` = Smokestack)  
- Web interface for configuration and beacon management  
- Supports manual and scheduled transmissions (every 5 minutes)  
- Built with Flask, `aprslib` and Bootstrap.

---

## 🚀 Installation

There are three ways to run lightAPRSinjector. Choose whichever fits best.

---

### Option 1: Docker (recommended)

The easiest way to get started. No Python setup required.

**1. Clone the repository**
```bash
git clone https://github.com/HochdruckHummer/lightAPRSinjector.git
cd lightAPRSinjector
```

**2. Build and start the container**
```bash
docker compose up -d
```

**3. Open in browser**

http://localhost:5000

Config and beacon data are stored in a persistent Docker volume (`aprs_data`), so your settings survive container restarts and updates.

**To update to the latest version:**
```bash
git pull
docker compose up -d --build
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

> **Note:** With the Web Editor, Portainer cannot build the image on its own — this only works once a pre-built image is available on Docker Hub. For a fully click-and-go setup without a terminal, use **Option 2a** instead.

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

If `beacons.json` does not exist, it will be created automatically when adding your first beacon.

---

## 🖥️ Usage

### Web Interface Features

<img width="691" height="786" alt="Screenshot_new_APRS_beacon_or_object" src="https://github.com/user-attachments/assets/21b5d3ce-31ef-40ef-b545-b5bb2ff26d9a" />

- **Edit config:** Set callsign, passcode, server and port
- **Add beacon or object:**
  - Name: max 9 characters (for APRS objects)
  - Position: latitude and longitude separated by comma (e.g. `52.2450,8.9057`) or selected on map
  - Symbol: select from 190 possible APRS symbols
  - Text: description (max 43 characters recommended)
  - Type: choose beacon or object
- **Toggle Active:** Enable/disable specific entries
- **Send Now:** Immediately transmit a beacon or object
- **Edit/Delete:** Modify or remove existing entries

---

## 🔁 Auto Transmission

A background thread automatically transmits all active entries every 5 minutes.

To change the interval, edit `app.py`:
```python
SEND_INTERVAL = 300  # seconds
```

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
