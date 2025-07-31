# lightAPRSinjector - a lightweight APRS Beacon and Object Manager by DL8YDP

A lightweight Flask web application to manage and send APRS position beacons and objects via APRS-IS. Designed for amateur radio operators, it offers a simple web interface to add, edit, activate, and send APRS data using configurable symbols (e.g., `/E` or `\E`), coordinates, and texts.

## ✨ Features

- Send APRS position beacons or objects over APRS-IS  
- Symbol support using `/` and `\` tables (e.g., `/E` = Eyeball, `\E` = Elevator)  
- Web interface for configuration and beacon management  
- Supports manual and scheduled transmissions (every 5 minutes)  
- Built with Flask and `aprslib`  

## 🚀 Installation and Setup


### 1. Clone the repository
git clone https://github.com/HochdruckHummer/lightAPRSinjector.git
cd aprs-beacon-manager

# 2. (Optional but recommended) Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install flask aprslib

# 4 Configuration
Create a file named config.json in the same directory as app.py:

{
  "callsign": "DL1ABC",
  "passcode": "12345",
  "server": "euro.aprs2.net",
  "port": 14580
}


callsign: Your full APRS callsign (e.g., DL1ABC-9 or DL1ABC)
passcode: Your APRS-IS passcode (generate it here)
server: Use euro.aprs2.net or another APRS-IS server
port: Default is 14580
If beacons.json does not exist, it will be created automatically when adding your first beacon.

Example format for beacons.json:

[
  {
    "name": "Home",
    "text": "DL8YDP Home QTH",
    "position": "52.1234,8.6543",
    "symbol": "/-",
    "type": "beacon",
    "active": true
  }
]
