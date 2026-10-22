# 📻 Sending on radio with Direwolf (beta)

lightAPRSinjector can hand its beacons and objects to a **KISS TNC**, which transmits
them on 144.800 MHz. The usual TNC is [Direwolf](https://github.com/wb2osz/direwolf),
a software modem that runs on a Raspberry Pi or any Linux computer connected to a radio.

```
lightAPRSinjector (e.g. in the basement)  ──LAN, TCP 8001──►  Direwolf (next to the radio)  ──USB──►  radio
```

The two do not have to run on the same machine. lightAPRSinjector only needs to reach
Direwolf's KISS port over the network.

> ⚠️ **This feature is in beta.** The packets are tested against Direwolf's
> decoder, but every radio setup is different. Check your first transmissions with a
> second receiver (e.g. a handheld in APRS mode) or on [aprs.fi](https://aprs.fi).

---

## 1. Set up Direwolf next to the radio

On a Raspberry Pi OS / Debian / Ubuntu machine connected to the radio:

```bash
sudo apt install direwolf
```

Pick the example configuration for your setup and copy it to `/etc/direwolf.conf`:

| Setup | File |
|---|---|
| Yaesu FT-991A with one USB cable | [`direwolf-ft991a.conf`](direwolf-ft991a.conf) |
| Handheld (Quansheng UV-K5, Baofeng …) with an AIOC cable | [`direwolf-aioc.conf`](direwolf-aioc.conf) |

Change the lines marked `CHANGE` (callsign, serial port). Then start Direwolf in a terminal:

```bash
direwolf -c /etc/direwolf.conf
```

It should end with `Ready to accept KISS TCP client application 0 on port 8001 ...`.

### Yaesu FT-991A settings

- Mode **DATA-FM** on **144.800 MHz**, moderate power (10–25 W is usually enough).
- In the menu (names as shown on the radio; the numbers differ between firmware versions):
  - `DATA PORT SELECT` → `USB`
  - `DATA PTT SELECT` → `RTS`
  - `FM PKT MODE` → `1200`
- Audio levels: in `alsamixer` (press F6 to pick the "USB Audio CODEC"), set the
  capture level so Direwolf reports an audio level of roughly 30–60 for received
  packets. Adjust the transmit level until other stations decode you reliably.

Please check these menu names against the FT-991A manual; they are from the
documentation, not tested on a radio by the developer.

### Handheld with AIOC

Set the radio to 144.800 MHz, squelch open just enough, VOX off. Plug the AIOC into
the K-plug. Recent AIOC firmware works with `PTT CM108`; for older firmware use the
serial PTT line shown in the example file.

---

## 2. Protect the KISS port

Direwolf's KISS port has **no password**. Anyone who can reach it can transmit with
your callsign. Never forward it to the internet, and allow only the lightAPRSinjector
host, for example with `ufw` on the Direwolf machine:

```bash
sudo ufw allow from 192.168.7.207 to any port 8001 proto tcp
sudo ufw deny 8001/tcp
sudo ufw enable
```

(Replace `192.168.7.207` with the address of the machine running lightAPRSinjector,
and make sure your SSH access is allowed before enabling `ufw`.)

---

## 3. Connect lightAPRSinjector

1. Open **Configuration → Radio (KISS TNC)**.
2. Enter the address of the Direwolf machine and port `8001`.
3. Click **Test TNC connection**. This only checks the network connection; nothing is transmitted.
4. Choose the digipeater path: `WIDE2-1` for a fixed station, `WIDE1-1,WIDE2-1` for a mobile one.
5. Choose the radio interval: at least 10 minutes, 30 minutes is a good value for fixed beacons and objects.
6. Switch on **Send on radio** and save.

Then edit a beacon or object, tick **📻 Radio** under *Send via*, and use **Send now**
for a first test. Direwolf shows the packet it transmits, for example:

```
[0L] DL8YDP>APRS,WIDE2-1:=5210.26N/00851.80E-Test
```

On radio the callsign SSID must be a number from 0 to 15 (e.g. `DL8YDP-10`).

---

## 4. Run Direwolf as a service

Once everything works, let systemd start Direwolf at boot. Create
`/etc/systemd/system/direwolf.service`:

```ini
[Unit]
Description=Direwolf TNC
After=sound.target network.target

[Service]
ExecStart=/usr/bin/direwolf -t 0 -c /etc/direwolf.conf
Restart=always
User=pi
SupplementaryGroups=audio dialout plugdev

[Install]
WantedBy=multi-user.target
```

Replace `pi` with your user name, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now direwolf
journalctl -u direwolf -f
```

---

## Legal note

Automatic transmissions are common practice on APRS, but the rules for unattended or
automatically operating stations depend on your country and licence. Please check them
for your setup.
