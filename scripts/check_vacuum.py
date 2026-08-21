"""
Diagnostic script for directly testing the local connection to the vacuum
via tinytuya, bypassing the Tuya cloud entirely.

Usage:
    export HOBOT_DEVICE_ID=...
    export HOBOT_DEVICE_IP=...
    export HOBOT_LOCAL_KEY=...
    python3 check_vacuum.py

Doesn't store any secrets in the file itself — reads them from environment
variables (the same ones exporter.py uses). Values can be taken from
router/S99hobot-exporter (if the exporter runs on a router or another
standalone device).
"""
import os
import sys

import tinytuya

DEVICE_ID = os.environ.get("HOBOT_DEVICE_ID")
IP = os.environ.get("HOBOT_DEVICE_IP")
LOCAL_KEY = os.environ.get("HOBOT_LOCAL_KEY")
PROTOCOL_VERSION = float(os.environ.get("HOBOT_PROTOCOL_VERSION", "3.3"))

if not all([DEVICE_ID, IP, LOCAL_KEY]):
    print("Error: not all required environment variables are set (HOBOT_DEVICE_ID, HOBOT_DEVICE_IP, HOBOT_LOCAL_KEY)")
    print("Hint: values can be taken from ../router/S99hobot-exporter and exported manually")
    sys.exit(1)

d = tinytuya.Device(DEVICE_ID, IP, LOCAL_KEY)
d.set_version(PROTOCOL_VERSION)

status = d.status()
print(status)
