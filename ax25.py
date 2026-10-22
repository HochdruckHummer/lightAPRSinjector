"""AX.25 UI frames in KISS framing, for sending APRS packets to a TNC (e.g. Direwolf).

An APRS packet on RF is an AX.25 "unnumbered information" frame:
destination, source and digipeater addresses, control 0x03, PID 0xF0 and the
APRS information field. KISS wraps it for the link to the TNC.
"""

import re
import socket
import threading

FEND = 0xC0   # KISS frame delimiter
FESC = 0xDB   # KISS escape
TFEND = 0xDC  # escaped FEND
TFESC = 0xDD  # escaped FESC

CONTROL_UI = 0x03
PID_NO_LAYER3 = 0xF0

# Base callsign up to 6 letters/digits, optional numeric SSID 0-15
AX25_ADDRESS_RE = re.compile(r"^([A-Z0-9]{1,6})(?:-([0-9]|1[0-5]))?$")


def parse_address(text):
    """Split 'DL8YDP-9' into ('DL8YDP', 9). Raises ValueError if it is not a valid AX.25 address."""
    match = AX25_ADDRESS_RE.match(text.strip().upper())
    if not match:
        raise ValueError(f"Not a valid AX.25 address: {text!r}")
    return match.group(1), int(match.group(2) or 0)


def is_valid_address(text):
    try:
        parse_address(text)
        return True
    except ValueError:
        return False


def encode_address(text, last=False, command=False):
    """Encode one 7-byte address field.

    The callsign is padded to 6 characters and every character is shifted left
    by one bit. The SSID byte holds the SSID, two reserved bits (set to 1),
    the command/has-been-repeated bit and the "last address" bit.
    """
    call, ssid = parse_address(text)
    encoded = bytes((ord(c) << 1) for c in call.ljust(6))
    ssid_byte = 0x60 | (ssid << 1)
    if command:
        ssid_byte |= 0x80
    if last:
        ssid_byte |= 0x01
    return encoded + bytes([ssid_byte])


def encode_ui_frame(source, destination, path, info):
    """Build an AX.25 UI frame (without flags and FCS; the TNC adds those)."""
    if len(path) > 8:
        raise ValueError("AX.25 allows at most 8 digipeaters")
    if isinstance(info, str):
        info = info.encode("utf-8")
    addresses = [encode_address(destination, command=True),
                 encode_address(source, last=not path)]
    for index, digi in enumerate(path):
        addresses.append(encode_address(digi, last=index == len(path) - 1))
    return b"".join(addresses) + bytes([CONTROL_UI, PID_NO_LAYER3]) + info


def kiss_wrap(frame, port=0):
    """Wrap an AX.25 frame as a KISS data frame for the given TNC port."""
    escaped = frame.replace(bytes([FESC]), bytes([FESC, TFESC])).replace(bytes([FEND]), bytes([FESC, TFEND]))
    return bytes([FEND, (port & 0x0F) << 4]) + escaped + bytes([FEND])


def kiss_unwrap(data):
    """Inverse of kiss_wrap for a single frame: returns (port, frame)."""
    if len(data) < 3 or data[0] != FEND or data[-1] != FEND:
        raise ValueError("Not a KISS frame")
    port = data[1] >> 4
    body = data[2:-1].replace(bytes([FESC, TFEND]), bytes([FEND])).replace(bytes([FESC, TFESC]), bytes([FESC]))
    return port, body


def decode_ui_frame(frame):
    """Decode an AX.25 UI frame into the usual text form 'SRC>DEST,PATH:info'."""
    addresses = []
    offset = 0
    while True:
        field = frame[offset:offset + 7]
        if len(field) < 7:
            raise ValueError("Truncated address field")
        call = "".join(chr(b >> 1) for b in field[:6]).strip()
        ssid = (field[6] >> 1) & 0x0F
        addresses.append(call + (f"-{ssid}" if ssid else ""))
        offset += 7
        if field[6] & 0x01:
            break
    if frame[offset:offset + 2] != bytes([CONTROL_UI, PID_NO_LAYER3]):
        raise ValueError("Not an APRS UI frame")
    info = frame[offset + 2:].decode("utf-8", errors="replace")
    destination, source, path = addresses[0], addresses[1], addresses[2:]
    return f"{source}>{','.join([destination] + path)}:{info}"


class KissTcpClient:
    """One long-lived connection to a KISS TNC.

    Direwolf reads every client connection in its own thread, so frames sent over
    separate, short connections can be transmitted out of order (e.g. an object's
    "kill" before its last position). Over a single connection they stay in order.
    The TNC also sends every packet it hears to its clients; a background thread
    reads and discards that data and notices when the TNC goes away.
    """

    def __init__(self, timeout=10):
        self.timeout = timeout
        self._lock = threading.Lock()
        self._sock = None
        self._target = None

    def _connect(self, host, port):
        sock = socket.create_connection((host, port), timeout=self.timeout)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._sock, self._target = sock, (host, port)
        threading.Thread(target=self._drain, args=(sock,), daemon=True).start()

    def _drain(self, sock):
        while True:
            try:
                if not sock.recv(4096):
                    break
            except socket.timeout:
                continue
            except OSError:
                break
        with self._lock:
            if self._sock is sock:
                self._close()

    def _close(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None

    def send(self, host, port, frames):
        data = b"".join(kiss_wrap(frame) for frame in frames)
        target = (host, int(port))
        with self._lock:
            if self._target != target:
                self._close()
            if self._sock is None:
                self._connect(*target)
            try:
                self._sock.sendall(data)
            except OSError:
                # The TNC was restarted since the last send: reconnect once and retry.
                self._close()
                self._connect(*target)
                self._sock.sendall(data)

    def close(self):
        with self._lock:
            self._close()


_client = KissTcpClient()


def send_kiss_tcp(host, port, frames):
    """Send KISS frames to a TNC over TCP (Direwolf's KISSPORT, usually 8001)."""
    _client.send(host, port, frames)


def check_kiss_tcp(host, port, timeout=5):
    """Only open and close a connection to the TNC. Nothing is transmitted."""
    with socket.create_connection((host, int(port)), timeout=timeout):
        pass
