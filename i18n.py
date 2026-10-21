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
    "Next automatic transmission in {time}",
    "Not sent yet",
    "Only shown in this list, for your overview.",
    "Please enter a callsign first.",
    "Sending now…",
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
        "Next automatic transmission in {time}": "Nächste automatische Aussendung in {time}",
        "Sending now…": "Wird gerade gesendet …",
        "'{name}' created.": "„{name}“ wurde angelegt.",
        "'{name}' saved.": "„{name}“ wurde gespeichert.",
        "'{name}' deleted.": "„{name}“ wurde gelöscht.",
        "'{name}' sent.": "„{name}“ wurde gesendet.",
        "Sending '{name}' failed: {error}": "Senden von „{name}“ fehlgeschlagen: {error}",

        # Send status errors
        "Invalid position": "Ungültige Position",
        "Login rejected – check callsign and passcode": "Anmeldung abgelehnt – Rufzeichen und Passcode prüfen",
        "APRS-IS server not reachable": "APRS-IS-Server nicht erreichbar",
        "Sending failed": "Senden fehlgeschlagen",

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
        "This is exactly what will be sent to APRS-IS.": "Genau das wird an APRS-IS gesendet.",
        "Active (sent automatically every {n} minutes)": "Aktiv (wird automatisch alle {n} Minuten gesendet)",
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
