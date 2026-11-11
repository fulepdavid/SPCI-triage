import os
import sys

# Never True on a patient-facing kiosk.
SIMULATE_DEVICES = False

TIMEOUT_MS = 3 * 60 * 1000

CLOSING_MS = 20 * 1000   # closing screen returns to the language selector after this

SHOW_IMAGE_OVERLAY = True

KIOSK = {
    "mouse_host": "10.64.4.235",         # measurement PC running the vendor UI
    "mouse_port": 5000,
    "hl7_host": "0.0.0.0",          # or the kiosk's LAN address
    "hl7_port": 5000,
    "monitor_ip": "10.64.5.217",    # only this address may send results
    "device_id": "KC574337852G",
}

# Read from the environment, not from the source code.
MOUSESYM_KEY = "mousesym"


def resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)