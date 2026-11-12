"""Starts a blood pressure measurement on the device UI and returns the result from the listener."""
import logging
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "mousesym" / "tools"))
from mousesym_client import MousesymClient, MousesymError

log = logging.getLogger("bp")
measurement_log = logging.getLogger("measurement")


class BloodPressureDevice:
    def __init__(self, mouse_host, mouse_port, mouse_key, listener, timeout=120):
        self.mouse_host, self.mouse_port, self.mouse_key = mouse_host, mouse_port, mouse_key
        self.listener = listener
        self.timeout = timeout

    def _click_start(self):
        c = MousesymClient(self.mouse_host, self.mouse_port, self.mouse_key,
                           verbose=False).connect()
        try:
            # Warm-up: the first move after power-on is lost, so MOVE 0 0 goes first.
            steps = [("MOVE 0 0", 0.1), 
            (f"CLICK 0 0", 0.5), 
            (f"CLICK 100 175", 0.5),
            (f"CLICK 220 75", 0)
            ]
            for cmd, pause in steps:
                resp = c.command(cmd)
                log.info("mouse %s -> %s", cmd, resp)
                if not resp.startswith("OK"):
                    raise MousesymError(f"{cmd} failed: {resp}")
                time.sleep(pause)
        finally:
            c.close()

    def measure(self):
        """Blocking. Call only from a worker thread."""
        window = self.listener.begin_window()
        try:
            self._click_start()
        except Exception:
            self.listener.close_window(window)
            raise
        log.info("measurement started, waiting for result")

        result = self.listener.wait_for_result(window, self.timeout)
        if result is None:
            log.error("timeout after %s s", self.timeout)
            raise TimeoutError("no complete blood pressure result received")

        measurement_log.info(
            "bp=%s/%s map=%s pulse_bp=%s spo2=%s pulse_spo2=%s device_time=%s",
            result["nibp_sys"], result["nibp_dia"], result["nibp_mean"],
            result["nibp_pulse"], result["spo2"], result["spo2_pulse"],
            result["measured_at"],
        )
        return result

    def start(self, result_queue):
        """Runs measure() in a thread and puts ('ok', result) or ('error', exc) on the queue."""
        def run():
            try:
                result_queue.put(("ok", self.measure()))
            except Exception as exc:
                log.exception("measurement failed")
                result_queue.put(("error", exc))
        threading.Thread(target=run, daemon=True).start()