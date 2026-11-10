"""Starts a blood pressure measurement and reads the result from the device service."""
import json
import logging
import sys
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent / "mousesym" / "tools"))
from mousesym_client import MousesymClient, MousesymError

log = logging.getLogger("bp")


class BloodPressureDevice:
    REQUIRED = ("nibp_sys", "nibp_dia", "pulse_rate")

    def __init__(self, mouse_host, mouse_port, mouse_key, start_button,
                 devices_url, device_id, timeout=120):
        self.mouse_host, self.mouse_port, self.mouse_key = mouse_host, mouse_port, mouse_key
        self.start_x, self.start_y = start_button
        self.device_id = device_id
        self.history_url = devices_url.replace("/api/devices", "/api/history")
        self.timeout = timeout

    def _history(self, limit=30):
        """Individual messages, oldest first. Each row holds only the vitals of that message."""
        url = f"{self.history_url}?device_id={quote(self.device_id)}&limit={limit}"
        with urllib.request.urlopen(url, timeout=3) as r:
            return json.loads(r.read())

    @staticmethod
    def _nibp_stamp(message):
        item = message.get("vitals", {}).get("nibp_sys")
        return item.get("observed_at") if item else None

    def _result_from(self, message, known):
        """Returns the result if this one message holds a new, final measurement."""
        vitals = message.get("vitals", {})
        if any(k not in vitals or vitals[k].get("status") != "F" for k in self.REQUIRED):
            return None
        stamp = vitals["nibp_sys"].get("observed_at")
        if not stamp or stamp in known:
            return None
        if vitals["nibp_dia"].get("observed_at") != stamp:
            return None
        return {
            "nibp_sys": vitals["nibp_sys"]["value"],
            "nibp_dia": vitals["nibp_dia"]["value"],
            "pulse_rate": vitals["pulse_rate"]["value"],
            "measured_at": stamp,
        }

    def _click_start(self):
        c = MousesymClient(self.mouse_host, self.mouse_port, self.mouse_key,
                           verbose=False).connect()
        try:
            # The first move after power-on is not reliably acted on, so MOVE 0 0 goes first.
            x, y = self.start_x, self.start_y
            for cmd, pause in [("MOVE 0 0", 0.3), (f"MOVE {x} {y}", 0.3), (f"CLICK {x} {y}", 0)]:
                resp = c.command(cmd)
                log.info("mouse %s -> %s", cmd, resp)
                if not resp.startswith("OK"):
                    raise MousesymError(f"{cmd} failed: {resp}")
                time.sleep(pause)
        finally:
            c.close()

    def measure(self):
        """Blocking. Call only from a worker thread."""
        # NIBP values that were already in the device stream before the click.
        known = {s for s in (self._nibp_stamp(m) for m in self._history()) if s}
        log.info("measure start: device=%s known_nibp=%d", self.device_id, len(known))

        self._click_start()

        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            time.sleep(1)
            try:
                rows = self._history()
            except OSError as exc:
                log.warning("history unreachable: %s", exc)
                continue
            for message in reversed(rows):          # newest first
                result = self._result_from(message, known)
                if result is not None:
                    log.info("result accepted, measured_at=%s", result["measured_at"])
                    return result

        log.error("timeout after %s s", self.timeout)
        raise TimeoutError("no complete blood pressure result received")

    def start(self, result_queue):
        """Runs measure() in a thread and puts ('ok', result) or ('error', exc) on the queue."""
        def run():
            try:
                result_queue.put(("ok", self.measure()))
            except Exception as exc:
                log.exception("measurement failed")
                result_queue.put(("error", exc))
        threading.Thread(target=run, daemon=True).start()