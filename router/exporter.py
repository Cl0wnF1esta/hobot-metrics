import os
import time
import logging
from logging.handlers import RotatingFileHandler

import tinytuya
from prometheus_client import start_http_server, Gauge, Info

# If HOBOT_LOG_FILE is set, logs are also written to a rotating file
# (10 MB x 3 files), in addition to console output. Useful when running
# directly (not in Docker), where there's no built-in log size limit
# like Docker's json-file driver provides.
LOG_FILE = os.environ.get("HOBOT_LOG_FILE", "")

log_handlers = [logging.StreamHandler()]
if LOG_FILE:
    log_handlers.append(
        RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=3)
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=log_handlers,
)
log = logging.getLogger("hobot-exporter")

# --- Configuration via environment variables ---
DEVICE_ID = os.environ["HOBOT_DEVICE_ID"]
DEVICE_IP = os.environ["HOBOT_DEVICE_IP"]
LOCAL_KEY = os.environ["HOBOT_LOCAL_KEY"]
PROTOCOL_VERSION = float(os.environ.get("HOBOT_PROTOCOL_VERSION", "3.3"))
POLL_INTERVAL = int(os.environ.get("HOBOT_POLL_INTERVAL", "15"))
EXPORTER_PORT = int(os.environ.get("HOBOT_EXPORTER_PORT", "9099"))

# --- Status code mapping from the device schema (dps) ---
ROBOT_STATUS_MAP = {
    "ok": "ok",
    "full_charged": "full_charged",
    "charging": "charging",
    "robot_here": "robot_here",
    "low_battery": "low_battery",
    "stuck": "stuck",
    "emergency_stop": "emergency_stop",
    "startup_fail": "startup_fail",
    "factory_fail": "factory_fail",
    "hw_fault": "hw_fault",
    "sensor_blinding": "sensor_blinding",
    "low_battery_charging": "low_battery_charging",
    "K_error": "K_error",
}

# --- Prometheus metrics ---
METRIC_PREFIX = "hobot"

battery_percent = Gauge(f"{METRIC_PREFIX}_battery_percent", "Battery charge, %")
clean_area_sqm = Gauge(f"{METRIC_PREFIX}_clean_area_sqm", "Area cleaned in the current session, sq.m")
clean_time_seconds = Gauge(f"{METRIC_PREFIX}_clean_time_seconds", "Duration of the current cleaning session, sec")
error_code = Gauge(f"{METRIC_PREFIX}_error_code", "Error code (0 = no errors)")
online = Gauge(f"{METRIC_PREFIX}_online", "Whether the last device poll succeeded (1/0)")
poll_duration_seconds = Gauge(f"{METRIC_PREFIX}_poll_duration_seconds", "Duration of the last device poll, sec")

# "Info" metric for string/enum states — convenient for filtering and building tables in Grafana
status_info = Info(f"{METRIC_PREFIX}_status", "Current string statuses of the vacuum")

# DPS codes as defined by the device schema (see m.life.device.ref.info.my.list)
DP_ROBOT_STATUS = "5"
DP_BATTERY = "6"
DP_MODE = "4"
DP_WORK_STATE = "108"
DP_ZONE_MODE = "109"
DP_WATER_TANK = "113"
DP_TRASH_CAN = "114"
DP_ERROR_CODE = "117"
DP_CLEAN_AREA = "16"
DP_CLEAN_TIME = "17"
DP_FIRMWARE = "107"


def build_device() -> tinytuya.Device:
    d = tinytuya.Device(DEVICE_ID, DEVICE_IP, LOCAL_KEY)
    d.set_version(PROTOCOL_VERSION)
    d.set_socketPersistent(True)
    return d


# While actively cleaning, the device often sends PARTIAL updates (only the
# dps that changed, e.g. a heartbeat) rather than a full snapshot every time.
# So we keep the last known values and only update whatever actually came
# back in a given response — everything else is left untouched.
known_dps: dict = {}


def poll_once(d: tinytuya.Device) -> None:
    start = time.monotonic()
    result = d.status()
    duration = time.monotonic() - start
    poll_duration_seconds.set(duration)

    dps = result.get("dps") if isinstance(result, dict) else None

    if not dps:
        log.warning("Empty or invalid response from device: %s", result)
        online.set(0)
        return

    online.set(1)
    known_dps.update(dps)  # merge the partial response on top of the known state

    if DP_BATTERY in known_dps:
        battery_percent.set(known_dps[DP_BATTERY])

    if DP_CLEAN_AREA in known_dps:
        clean_area_sqm.set(known_dps[DP_CLEAN_AREA])

    if DP_CLEAN_TIME in known_dps:
        clean_time_seconds.set(known_dps[DP_CLEAN_TIME])

    if DP_ERROR_CODE in known_dps:
        error_code.set(known_dps[DP_ERROR_CODE])

    status_info.info({
        "robot_status": str(known_dps.get(DP_ROBOT_STATUS, "")),
        "mode": str(known_dps.get(DP_MODE, "")),
        "work_state": str(known_dps.get(DP_WORK_STATE, "")),
        "zone_mode": str(known_dps.get(DP_ZONE_MODE, "")),
        "water_tank": str(known_dps.get(DP_WATER_TANK, "")),
        "trash_can": str(known_dps.get(DP_TRASH_CAN, "")),
        "firmware": str(known_dps.get(DP_FIRMWARE, "")),
    })

    log.info(
        "OK: battery=%s%% status=%s work_state=%s error=%s (%.2fs)",
        known_dps.get(DP_BATTERY), known_dps.get(DP_ROBOT_STATUS), known_dps.get(DP_WORK_STATE),
        known_dps.get(DP_ERROR_CODE), duration,
    )


def main() -> None:
    log.info("Starting hobot-exporter on port %d, polling every %d sec", EXPORTER_PORT, POLL_INTERVAL)
    start_http_server(EXPORTER_PORT)

    d = build_device()

    while True:
        try:
            poll_once(d)
        except Exception as e:
            log.error("Error polling device: %s", e)
            online.set(0)
            # In case the connection dropped — rebuild the device object
            try:
                d = build_device()
            except Exception as e2:
                log.error("Failed to reconnect: %s", e2)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
