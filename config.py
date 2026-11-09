import os
import sys

# Never True on a patient-facing kiosk.
SIMULATE_DEVICES = False

TIMEOUT_MS = 3 * 60 * 1000
SHOW_IMAGE_OVERLAY = True

KIOSK = {
    "mouse_host": "10.64.4.235",         # measurement PC running the vendor UI
    "mouse_port": 5000,
    "bp_start_button": (220, 75),        # PLACEHOLDER: calibrate on the measurement PC
    "devices_url": "http://127.0.0.1:8080/api/devices",
    "device_id": "KC574337852G",
}

# Read from the environment, not from the source code.
MOUSESYM_KEY = "mousesym"


def resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)