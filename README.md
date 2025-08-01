# lightAPRSinjector - a lightweight APRS Beacon and Object Manager by DL8YDP

A lightweight Flask web application to manage and send APRS position beacons and objects via APRS-IS. Designed for amateur radio operators, it offers a modern and simple (Bootstrap) web interface to add, edit, activate, and send APRS data using configurable symbols (e.g., `/E` or `\E`), coordinates, and texts.

## ✨ Features

- Send APRS position beacons or objects over APRS-IS  
- Symbol support using `/` and `\` tables (e.g., `/E` = Eyeball, `\E` = Smokestack)  
- Web interface for configuration and beacon management  
- Supports manual and scheduled transmissions (every 5 minutes)  
- Built with Flask, `aprslib`  and Bootstrap.

## 🚀 Installation and Setup


### 1. Clone the repository
```bash
git clone https://github.com/HochdruckHummer/lightAPRSinjector.git
cd aprs-beacon-manager
```
### 2. (Optional but recommended) Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
### 3. Install dependencies
```bash

pip install flask aprslib
```


## 4 Configuration
Create a file named config.json in the same directory as app.py:


```json
{
  "callsign": "DL8YDP",
  "passcode": "12345",
  "server": "euro.aprs2.net",
  "port": 14580
}
```

callsign: Your full APRS callsign (e.g., DL8YDP or DL8YDP-9)


passcode: Your APRS-IS passcode (generate it [here](https://apps.magicbug.co.uk/passcode/))


server: Use euro.aprs2.net or another APRS-IS server


port: Default is 14580


If beacons.json does not exist, it will be created automatically when adding your first beacon.

Example format for beacons.json:
```json
[
  {
    "name": "Home",
    "text": "DL8YDP Home QTH",
    "position": "52.2450,8.9057",
    "symbol": "/-",
    "type": "beacon",
    "active": true
  }
]
```
## 🖥️ Usage

Start the app:
```bash
python app.py
```

Open the app in your browser:
http://localhost:5000 (or access it via LAN if running on a Raspberry Pi or server)

### Web Interface Features
Edit config: Set your callsign, passcode, server and port

Add beacon or object:

Name: max 9 characters (for APRS objects)

Position: latitude and longitude separated by comma (e.g., 52.2450,8.9057)

Symbol: two-character APRS symbol (e.g., /E, \E)

Text: description (max 43 characters recommended)

Type: choose beacon or object

Toggle Active: Enable/disable specific entries

Send Now: Immediately transmit a beacon or object

Edit/Delete: Modify or remove existing entries

## 🔁 Auto Transmission

A background thread automatically transmits all active entries every 5 minutes.

Change interval in app.py:

SEND_INTERVAL = 300  # seconds

## 🛠️ Notes

APRS object names are limited to 9 characters

Symbol codes consist of two characters: / or \ plus the actual symbol (e.g., /E)

The first character determines the symbol table; the second is the symbol itself

## 📜 License

This project is licensed under the MIT License.

## 📡 Author

Created by DL8YDP
Pull requests and contributions are welcome!
