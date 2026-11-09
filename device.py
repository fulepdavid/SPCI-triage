"""Starts a blood pressure measurement on the device UI and waits for the result."""
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "mousesym" / "tools"))
from mousesym_client import MousesymClient, MousesymError


class BloodPressureDevice:
    REQUIRED = ("nibp_sys", "nibp_dia", "pulse_rate")

    def __init__(self, mouse_host, mouse_port, mouse_key, start_button,
                 devices_url, device_id, timeout=120):
        self.mouse_host, self.mouse_port, self.mouse_key = mouse_host, mouse_port, mouse_key
        self.start_x, self.start_y = start_button
        self.devices_url, self.device_id = devices_url, device_id
        self.timeout = timeout

    def _device_row(self):
        with urllib.request.urlopen(self.devices_url, timeout=3) as r:
            rows = json.loads(r.read())
        return next((row for row in rows if row["device_id"] == self.device_id), None)

    def _baseline(self, row):
        """Device-side timestamp of the last NIBP systolic value, or None."""
        if not row:
            return None
        return row["vitals"].get("nibp_sys", {}).get("observed_at") or None

    def _complete_result(self, row, baseline):
        """Returns the result only for a new measurement with all required vitals, final status."""
        vitals = row["vitals"]
        items = [vitals.get(k) for k in self.REQUIRED]
        if any(item is None for item in items):
            return None
        if any(item.get("status") != "F" for item in items):
            return None
        stamps = {item.get("observed_at") for item in items}
        if len(stamps) != 1:
            return None
        stamp = stamps.pop()
        if not stamp or stamp == baseline:
            return None
        return {k: vitals[k]["value"] for k in self.REQUIRED}

    def _click_start(self):
        c = MousesymClient(self.mouse_host, self.mouse_port, self.mouse_key,
                           verbose=False).connect()
        try:
            if not c.command(f"MOVE {self.start_x} {self.start_y}").startswith("OK"):
                raise MousesymError("MOVE failed")
            time.sleep(0.3)  # let the vendor UI register the hover
            if not c.command(f"CLICK {self.start_x} {self.start_y}").startswith("OK"):
                raise MousesymError("CLICK failed")
        finally:
            c.close()

    def measure(self):
        """Blocking. Call only from a worker thread."""
        baseline = self._baseline(self._device_row())
        self._click_start()
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            time.sleep(1)
            try:
                row = self._device_row()
            except OSError:
                continue
            if row:
                result = self._complete_result(row, baseline)
                if result is not None:
                    return result
        raise TimeoutError("no complete blood pressure result received")

    def start(self, result_queue):
        """Runs measure() in a thread and puts ('ok', result) or ('error', exc) on the queue."""
        def run():
            try:
                result_queue.put(("ok", self.measure()))
            except Exception as exc:
                result_queue.put(("error", exc))
        threading.Thread(target=run, daemon=True).start()