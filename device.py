"""Starts a blood pressure measurement on the device UI and returns the result from the listener."""
import logging
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "mousesym" / "tools"))
from mousesym_client import MousesymClient, MousesymError

log = logging.getLogger("bp")


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
            (f"CLICK 0 0", 0.1), 
            (f"CLICK 100 175", 0.1),
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
        window = self.listener.begin_window()     # open before the click
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