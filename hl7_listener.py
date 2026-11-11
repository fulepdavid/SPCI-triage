"""HL7 listener inside the kiosk.

Accepts MLLP-framed ORU^R01 messages from the monitor and ACKs every message.
Keeps no files and no history. Collects a blood pressure result only while a
measurement window is open.
"""
import logging
import socket
import threading
from datetime import datetime

from hl7_parser import parse

log = logging.getLogger("hl7")

MLLP_START = b"\x0b"
MLLP_END = b"\x1c"
CR = b"\r"
MAX_BUFFER = 1_000_000          # drop connections that send junk without a frame end
NIBP_KEYS = ("nibp_sys", "nibp_dia", "pulse_rate")

# Codes the default parser table doesn't map. The keys are what device.py reads.
EXTRA_CODES = {
    "150021": {"key": "nibp_sys", "unit": "mmHg"},
    "150022": {"key": "nibp_dia", "unit": "mmHg"},
    "149546": {"key": "pulse_rate", "unit": "beats/min"},
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
    """Returns the result only if all three values are final and share one timestamp."""
    if any(k not in vitals or vitals[k].get("status") != "F" for k in NIBP_KEYS):
        return None
    stamp = vitals["nibp_sys"].get("observed_at")
    if not stamp or {vitals[k].get("observed_at") for k in NIBP_KEYS} != {stamp}:
        return None
    return {
        "nibp_sys": vitals["nibp_sys"]["value"],
        "nibp_dia": vitals["nibp_dia"]["value"],
        "pulse_rate": vitals["pulse_rate"]["value"],
        "measured_at": stamp,
    }


class Hl7Listener:
    def __init__(self, host, port, device_id, allowed_ip=None):
        self.host, self.port = host, port
        self.device_id = device_id
        self.allowed_ip = allowed_ip        # only the monitor may connect
        self._config = {"extra_codes": EXTRA_CODES}
        self._lock = threading.Lock()
        self._last_stamp = None             # NIBP timestamp of the newest message
        self._window = None                 # open while a measurement waits for a result
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
                return                      # socket closed
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
        except Exception as exc:            # log the error type only, never the content
            log.warning("message rejected: %s", type(exc).__name__)
            return _frame(_ack(control_id, "AR"))
        self._offer(row)
        return _frame(_ack(control_id, "AA"))

    def _offer(self, row):
        if row["device_id"] != self.device_id:
            return
        vitals = row["vitals"]
        stamp = vitals.get("nibp_sys", {}).get("observed_at") or None
        result = _complete_result(vitals)
        with self._lock:
            if stamp:
                self._last_stamp = stamp
            window = self._window
            if window is None or window["result"] is not None or result is None:
                return
            if result["measured_at"] == window["baseline"]:
                return                      # the value that was already there before the click
            window["result"] = result
            window["event"].set()
            log.info("measurement result received")

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