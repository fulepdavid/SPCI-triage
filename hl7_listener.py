"""HL7 listener inside the kiosk.

Accepts MLLP-framed messages from the monitor and ACKs every one.
Keeps no message history. Keeps only the newest SpO2 and pulse readings,
and collects a blood pressure result while a measurement window is open.
"""
import logging
import socket
import threading
import time
from datetime import datetime

from hl7_parser import parse

log = logging.getLogger("hl7")

MLLP_START = b"\x0b"
MLLP_END = b"\x1c"
CR = b"\r"
MAX_BUFFER = 1_000_000
NIBP_KEYS = ("nibp_sys", "nibp_dia", "nibp_mean", "nibp_pulse")
SPO2_MAX_AGE = 10.0       # seconds; older SpO2 readings are not attached to a result

EXTRA_CODES = {
    "150021": {"key": "nibp_sys", "unit": "mmHg"},
    "150022": {"key": "nibp_dia", "unit": "mmHg"},
    "150023": {"key": "nibp_mean", "unit": "mmHg"},
    "149546": {"key": "nibp_pulse", "unit": "beats/min"},
    "150456": {"key": "spo2", "unit": "%"},
    "149522": {"key": "pulse_rate", "unit": "beats/min"},
}


def _frame(text):
    return MLLP_START + text.encode("utf-8") + MLLP_END + CR


def _control_id(text):
    msh = text.split("\r", 1)[0].split("|")
    return msh[9] if len(msh) > 9 else "UNKNOWN"


def _ack(control_id, code):
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return (f"MSH|^~\\&|TRIAGE|TRIAGE|||{ts}||ACK^R01^ACK|ACK{ts}|P|2.6\r"
            f"MSA|{code}|{control_id}\r")


def _complete_result(vitals):
    """Returns the NIBP values only if all four are final and share one timestamp."""
    if any(k not in vitals or vitals[k].get("status") != "F" for k in NIBP_KEYS):
        return None
    stamp = vitals["nibp_sys"].get("observed_at")
    if not stamp or {vitals[k].get("observed_at") for k in NIBP_KEYS} != {stamp}:
        return None
    return {
        "nibp_sys": vitals["nibp_sys"]["value"],
        "nibp_dia": vitals["nibp_dia"]["value"],
        "nibp_mean": vitals["nibp_mean"]["value"],
        "nibp_pulse": vitals["nibp_pulse"]["value"],
        "measured_at": stamp,
    }


class Hl7Listener:
    def __init__(self, host, port, device_id, allowed_ip=None):
        self.host, self.port = host, port
        self.device_id = device_id
        self.allowed_ip = allowed_ip
        self._config = {"extra_codes": EXTRA_CODES}
        self._lock = threading.Lock()
        self._last_stamp = None     # NIBP timestamp of the newest message
        self._spo2 = {}             # key -> (value, time received), monotonic clock
        self._window = None
        self._server = None

    # ---- server ---------------------------------------------------------
    def start(self):
        self._server = socket.create_server((self.host, self.port))
        threading.Thread(target=self._accept_loop, name="hl7-accept", daemon=True).start()
        log.info("HL7 listening on %s:%s", self.host, self.port)

    def _accept_loop(self):
        while True:
            try:
                conn, addr = self._server.accept()
            except OSError:
                return
            if self.allowed_ip and addr[0] != self.allowed_ip:
                log.warning("connection from unexpected address rejected")
                conn.close()
                continue
            threading.Thread(target=self._serve, args=(conn, addr[0]), daemon=True).start()

    def _serve(self, conn, ip):
        buffer = b""
        with conn:
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                buffer += chunk
                if len(buffer) > MAX_BUFFER:
                    log.warning("buffer limit exceeded, connection closed")
                    return
                while MLLP_END in buffer:
                    frame, buffer = buffer.split(MLLP_END, 1)
                    frame = frame.replace(MLLP_START, b"").strip(b"\r\n")
                    if frame:
                        conn.sendall(self._handle(frame.decode("utf-8", "replace"), ip))

    # ---- messages -------------------------------------------------------
    def _handle(self, text, ip):
        control_id = _control_id(text)
        try:
            row = parse(text, ip, self._config)
        except Exception as exc:
            log.warning("message rejected: %s", type(exc).__name__)
            return _frame(_ack(control_id, "AR"))
        self._offer(row)
        return _frame(_ack(control_id, "AA"))

    def _remember_spo2(self, vitals):
        now = time.monotonic()
        for key in ("spo2", "pulse_rate"):
            item = vitals.get(key)
            if item and item.get("status") == "F" and item.get("value") is not None:
                self._spo2[key] = (item["value"], now)

    def _recent(self, key):
        item = self._spo2.get(key)
        if item is None:
            return None
        value, seen = item
        return value if time.monotonic() - seen <= SPO2_MAX_AGE else None

    def _offer(self, row):
        if row["device_id"] != self.device_id:
            return
        vitals = row["vitals"]
        with self._lock:
            self._remember_spo2(vitals)
            stamp = vitals.get("nibp_sys", {}).get("observed_at") or None
            if stamp:
                self._last_stamp = stamp
            window = self._window
            if window is None or window["result"] is not None:
                return
            result = _complete_result(vitals)
            if result is None or result["measured_at"] == window["baseline"]:
                return
            result["spo2"] = self._recent("spo2")
            result["spo2_pulse"] = self._recent("pulse_rate")
            if result["spo2"] is None:
                log.warning("no recent SpO2 reading for this blood pressure result")
            window["result"] = result
            window["event"].set()

    # ---- measurement window ---------------------------------------------
    def begin_window(self):
        """Call before the click, so no result can be missed."""
        with self._lock:
            self._window = {"baseline": self._last_stamp, "result": None,
                            "event": threading.Event()}
            return self._window

    def wait_for_result(self, window, timeout):
        window["event"].wait(timeout)
        self.close_window(window)
        return window["result"]

    def close_window(self, window):
        with self._lock:
            if self._window is window:
                self._window = None