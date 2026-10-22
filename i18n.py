"""Minimal translations: the English text is the key, other languages map it to their text.

To add a language, add it to LANGUAGES and add a dictionary to TRANSLATIONS.
Missing entries fall back to English.
"""

from flask import has_request_context, request

DEFAULT_LANGUAGE = "en"
LANGUAGES = {"en": "English", "de": "Deutsch"}

# Texts used by JavaScript; they are handed to the page as window.APP.i18n
JS_STRINGS = [
    'Do you really want to delete "{name}"?',
    "Failed {time}: {error}",
    "Next automatic transmission: {times}",
    "Not sent yet",
    "Not sent: radio is switched off",
    "now",
    "Only shown in this list, for your overview.",
    "Please enter a callsign first.",
    "Sent {time}",
    "Shown on the map. Letters, digits and spaces, max. {n}.",
    "Testing connection…",
    "The test could not be run. Please reload the page.",
    "{n} / {max} characters",
]

TRANSLATIONS = {
    "de": {
        # Header, footer, general
        "a lightweight APRS Beacon and Object Manager by DL8YDP": "ein schlanker APRS-Baken- und Objektmanager von DL8YDP",
        "Configuration": "Konfiguration",
        "Language": "Sprache",
        "Dark mode": "Dunkelmodus",
        "Logout": "Abmelden",
        "Close": "Schließen",
        "Cancel": "Abbrechen",
        "Save": "Speichern",
        "Create": "Anlegen",
        "Edit": "Bearbeiten",
        "Delete": "Löschen",
        "Version": "Version",
        "here": "hier",
        "Donate a beer": "Spendier ein Bier",
        "Donate a beer via PayPal": "Spendier ein Bier per PayPal",
        "If this project helps you, feel free to donate a beer 🍺": "Wenn dir das Projekt hilft, spendier gern ein Bier 🍺",

        # Login
        "Login": "Anmeldung",
        "Username": "Benutzername",
        "Password": "Passwort",
        "Stay logged in for 30 days": "30 Tage angemeldet bleiben",
        "Log in": "Anmelden",
        "The password is set with WEB_PASSWORD, or shown in the log on first start.":
            "Das Passwort wird über WEB_PASSWORD festgelegt oder beim ersten Start im Log angezeigt.",
        "Wrong username or password.": "Benutzername oder Passwort ist falsch.",
        "Too many failed attempts. Please wait {n} minutes.": "Zu viele Fehlversuche. Bitte warte {n} Minuten.",
        "You have been logged out.": "Du wurdest abgemeldet.",
        "Your session expired. Please try again.": "Deine Sitzung ist abgelaufen. Bitte versuche es erneut.",

        # Overview
        "Create new beacon / object": "Neue Bake / neues Objekt",
        "Map of all beacons and objects": "Karte aller Baken und Objekte",
        "Current beacons and objects": "Aktuelle Baken und Objekte",
        "{active} of {total} active": "{active} von {total} aktiv",
        "Active": "Aktiv",
        "Inactive": "Inaktiv",
        "Activate": "Aktivieren",
        "Deactivate": "Deaktivieren",
        "Beacon": "Bake",
        "Object": "Objekt",
        "Send now": "Jetzt senden",
        "More actions": "Weitere Aktionen",
        "Show on map": "Auf der Karte zeigen",
        "No beacons or objects yet.": "Noch keine Baken oder Objekte.",
        "Create the first one": "Lege die erste an",
        "Delete entry": "Eintrag löschen",
        'Do you really want to delete "{name}"?': "Möchtest du „{name}“ wirklich löschen?",
        "The object will also be removed from APRS maps like aprs.fi.":
            "Das Objekt wird dabei auch von APRS-Karten wie aprs.fi entfernt.",
        "Not sent yet": "Noch nicht gesendet",
        "Sent {time}": "Gesendet {time}",
        "Failed {time}: {error}": "Fehlgeschlagen {time}: {error}",
        "Next automatic transmission: {times}": "Nächste automatische Aussendung: {times}",
        "Not sent: radio is switched off": "Nicht gesendet: Funk ist ausgeschaltet",
        "now": "jetzt",
        "'{name}' created.": "„{name}“ wurde angelegt.",
        "'{name}' saved.": "„{name}“ wurde gespeichert.",
        "'{name}' deleted.": "„{name}“ wurde gelöscht.",
        "'{name}' sent ({channel}).": "„{name}“ wurde gesendet ({channel}).",
        "Sending '{name}' failed ({channel}): {error}": "Senden von „{name}“ fehlgeschlagen ({channel}): {error}",
        "'{name}' has no active way to send. Radio is switched off in the configuration.":
            "„{name}“ hat keinen aktiven Sendeweg. Funk ist in der Konfiguration ausgeschaltet.",
        "Internet": "Internet",
        "Radio": "Funk",

        # Send status errors
        "Invalid position": "Ungültige Position",
        "Login rejected – check callsign and passcode": "Anmeldung abgelehnt – Rufzeichen und Passcode prüfen",
        "APRS-IS server not reachable": "APRS-IS-Server nicht erreichbar",
        "Sending failed": "Senden fehlgeschlagen",
        "TNC not reachable": "TNC nicht erreichbar",
        "Callsign not usable on radio (SSID must be 0-15)": "Rufzeichen auf Funk nicht verwendbar (SSID muss 0–15 sein)",

        # Beacon form
        "New beacon or object": "Neue Bake oder neues Objekt",
        "Create new APRS beacon or object": "Neue APRS-Bake oder neues Objekt anlegen",
        "Edit APRS beacon or object": "APRS-Bake oder Objekt bearbeiten",
        "Type": "Typ",
        "A position report for your own station, sent with your callsign.":
            "Eine Positionsmeldung für deine eigene Station, gesendet mit deinem Rufzeichen.",
        "A marker for something else, e.g. an event, a club station or a repeater. It appears on the map under its own name.":
            "Eine Markierung für etwas anderes, z. B. eine Veranstaltung, eine Clubstation oder ein Relais. "
            "Sie erscheint unter eigenem Namen auf der Karte.",
        "Name": "Name",
        "Only shown in this list, for your overview.": "Wird nur in dieser Liste angezeigt, zur Übersicht.",
        "Shown on the map. Letters, digits and spaces, max. {n}.":
            "Wird auf der Karte angezeigt. Buchstaben, Ziffern und Leerzeichen, max. {n}.",
        "{n} / {max} characters": "{n} / {max} Zeichen",
        "Text": "Text",
        "Longer than {n} characters – many devices cut off the rest.":
            "Länger als {n} Zeichen – viele Geräte schneiden den Rest ab.",
        "Position (Lat,Lon)": "Position (Breite,Länge)",
        "Click on the map or drag the marker to set the position.":
            "Klicke in die Karte oder ziehe den Marker, um die Position festzulegen.",
        "Symbol": "Symbol",
        "No symbol selected": "Kein Symbol ausgewählt",
        "Search symbols, e.g. house": "Symbole suchen, z. B. Haus",
        "Symbol table": "Symboltabelle",
        "Primary": "Primär",
        "Alternate": "Alternativ",
        "No symbols found.": "Keine Symbole gefunden.",
        "Packet preview": "Paketvorschau",
        "This is exactly what will be sent.": "Genau das wird gesendet.",
        "Active (sent automatically)": "Aktiv (wird automatisch gesendet)",
        "Send via": "Senden über",
        "Internet (APRS-IS)": "Internet (APRS-IS)",
        "Radio is switched off in the configuration. Entries marked for radio are only sent there once it is enabled.":
            "Funk ist in der Konfiguration ausgeschaltet. Einträge mit Funk werden dort erst gesendet, wenn er eingeschaltet ist.",
        "Choose at least one way to send: Internet or radio.": "Wähle mindestens einen Sendeweg: Internet oder Funk.",
        "Enter a valid position or click on the map.": "Gib eine gültige Position ein oder klicke in die Karte.",

        # Form validation
        "Invalid type.": "Ungültiger Typ.",
        "Name is required.": "Bitte gib einen Namen ein.",
        "Object names may have at most {n} characters.": "Objektnamen dürfen höchstens {n} Zeichen lang sein.",
        "Object names may only contain ASCII characters.": "Objektnamen dürfen nur ASCII-Zeichen enthalten (keine Umlaute).",
        "Name may have at most {n} characters.": "Der Name darf höchstens {n} Zeichen lang sein.",
        "Text may have at most {n} characters.": "Der Text darf höchstens {n} Zeichen lang sein.",
        "Position must be 'latitude,longitude' in decimal degrees, e.g. 52.2450,8.9057.":
            "Die Position muss als „Breite,Länge“ in Dezimalgrad angegeben werden, z. B. 52.2450,8.9057.",
        "Please choose a symbol.": "Bitte wähle ein Symbol.",

        # Configuration
        "Configuration saved.": "Konfiguration gespeichert.",
        "Callsign": "Rufzeichen",
        "Your callsign, optionally with SSID, e.g. DL8YDP or DL8YDP-9.":
            "Dein Rufzeichen, optional mit SSID, z. B. DL8YDP oder DL8YDP-9.",
        "Passcode": "Passcode",
        "Stored – leave empty to keep": "Gespeichert – leer lassen zum Beibehalten",
        "Generate from callsign": "Aus Rufzeichen berechnen",
        "The passcode is calculated locally from your callsign.": "Der Passcode wird lokal aus deinem Rufzeichen berechnet.",
        "If the result seems wrong, you can also generate it manually":
            "Falls das Ergebnis falsch erscheint, kannst du ihn auch manuell erzeugen",
        "Please enter a callsign first.": "Bitte gib zuerst ein Rufzeichen ein.",
        "Server": "Server",
        "Port": "Port",
        "Test connection": "Verbindung testen",
        "Testing connection…": "Verbindung wird getestet …",
        "The test could not be run. Please reload the page.":
            "Der Test konnte nicht ausgeführt werden. Bitte lade die Seite neu.",
        "Connected and logged in as {call} at {server}:{port}.": "Verbunden und als {call} bei {server}:{port} angemeldet.",
        "The server rejected the login. Check callsign and passcode.":
            "Der Server hat die Anmeldung abgelehnt. Prüfe Rufzeichen und Passcode.",
        "Could not connect to {server}:{port}.": "Keine Verbindung zu {server}:{port} möglich.",
        "Active entries are sent automatically every {n} minutes (environment variable SEND_INTERVAL).":
            "Aktive Einträge werden automatisch alle {n} Minuten gesendet (Umgebungsvariable SEND_INTERVAL).",
        "Invalid callsign (e.g. DL8YDP or DL8YDP-9).": "Ungültiges Rufzeichen (z. B. DL8YDP oder DL8YDP-9).",
        "Passcode must be a number.": "Der Passcode muss eine Zahl sein.",
        "Invalid server name.": "Ungültiger Servername.",

        # Radio configuration
        "Radio (KISS TNC)": "Funk (KISS-TNC)",
        "Setup guide": "Anleitung",
        "This feature is in beta.": "Diese Funktion ist in der Beta-Phase.",
        "It has been tested with Direwolf, but not yet with every radio. Check your first transmissions with a second receiver or on aprs.fi, and please report problems on GitHub.":
            "Sie wurde mit Direwolf getestet, aber noch nicht mit jedem Funkgerät. Prüfe deine ersten Aussendungen mit einem "
            "zweiten Empfänger oder auf aprs.fi und melde Probleme bitte auf GitHub.",
        "Sends entries over a TNC such as Direwolf on a computer connected to your radio. It can run anywhere in your network.":
            "Sendet Einträge über einen TNC wie Direwolf auf einem Rechner, der mit deinem Funkgerät verbunden ist. "
            "Er kann irgendwo in deinem Netzwerk stehen.",
        "Send on radio": "Über Funk senden",
        "TNC address": "TNC-Adresse",
        "KISS port": "KISS-Port",
        "Digipeater path": "Digipeater-Pfad",
        "WIDE2-1 suits a fixed station, WIDE1-1,WIDE2-1 a mobile one. Leave empty to send without digipeaters.":
            "WIDE2-1 passt für eine feste Station, WIDE1-1,WIDE2-1 für eine mobile. Leer lassen, um ohne Digipeater zu senden.",
        "Radio interval (minutes)": "Funk-Intervall (Minuten)",
        "144.800 MHz is shared by everyone. 10 minutes is the minimum, 30 minutes is a good value for fixed beacons and objects.":
            "144,800 MHz teilen sich alle. 10 Minuten sind das Minimum, 30 Minuten ein guter Wert für feste Baken und Objekte.",
        "Test TNC connection": "TNC-Verbindung testen",
        "Only checks the network connection. Nothing is transmitted.": "Prüft nur die Netzwerkverbindung. Es wird nichts gesendet.",
        "Please enter the address and port of the TNC.": "Bitte gib Adresse und Port des TNC ein.",
        "Could not connect to the TNC at {host}:{port}. Is Direwolf running?":
            "Keine Verbindung zum TNC unter {host}:{port}. Läuft Direwolf?",
        "The TNC at {host}:{port} accepts connections. Nothing was transmitted.":
            "Der TNC unter {host}:{port} nimmt Verbindungen an. Es wurde nichts gesendet.",
        "Invalid TNC address.": "Ungültige TNC-Adresse.",
        "TNC port must be a number between 1 and 65535.": "Der TNC-Port muss eine Zahl zwischen 1 und 65535 sein.",
        "Invalid path. Use up to {n} entries like WIDE1-1,WIDE2-1, or leave it empty.":
            "Ungültiger Pfad. Bis zu {n} Einträge wie WIDE1-1,WIDE2-1 verwenden oder leer lassen.",
        "The radio interval must be between {min} and {max} minutes.":
            "Das Funk-Intervall muss zwischen {min} und {max} Minuten liegen.",
        "On radio the SSID must be a number from 0 to 15 (e.g. DL8YDP-10).":
            "Auf Funk muss die SSID eine Zahl von 0 bis 15 sein (z. B. DL8YDP-10).",
        "Port must be a number between 1 and 65535.": "Der Port muss eine Zahl zwischen 1 und 65535 sein.",
    },
}


def get_language():
    """Language of the current request (cookie set by the language switch)."""
    if has_request_context():
        lang = request.cookies.get("lang")
        if lang in LANGUAGES:
            return lang
    return DEFAULT_LANGUAGE


def _(text, **values):
    """Translate an English text and fill in {placeholders}."""
    translated = TRANSLATIONS.get(get_language(), {}).get(text, text)
    return translated.format(**values) if values else translated


def js_translations():
    return {key: _(key) for key in JS_STRINGS}
