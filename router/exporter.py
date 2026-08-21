import os
import time
import logging
from logging.handlers import RotatingFileHandler

import tinytuya
from prometheus_client import start_http_server, Gauge, Info

# Если задан HOBOT_LOG_FILE — логи пишутся в файл с ротацией (10 МБ x 3 файла),
# помимо вывода в консоль. Полезно при запуске напрямую (не в Docker), где
# нет встроенного ограничения на размер логов, как у json-file драйвера Docker.
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

# --- Конфигурация через переменные окружения ---
DEVICE_ID = os.environ["HOBOT_DEVICE_ID"]
DEVICE_IP = os.environ["HOBOT_DEVICE_IP"]
LOCAL_KEY = os.environ["HOBOT_LOCAL_KEY"]
PROTOCOL_VERSION = float(os.environ.get("HOBOT_PROTOCOL_VERSION", "3.3"))
POLL_INTERVAL = int(os.environ.get("HOBOT_POLL_INTERVAL", "15"))
EXPORTER_PORT = int(os.environ.get("HOBOT_EXPORTER_PORT", "9099"))

# --- Расшифровка кодов состояния из схемы устройства (dps) ---
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

# --- Метрики Prometheus ---
METRIC_PREFIX = "hobot"

battery_percent = Gauge(f"{METRIC_PREFIX}_battery_percent", "Заряд батареи, %")
clean_area_sqm = Gauge(f"{METRIC_PREFIX}_clean_area_sqm", "Убранная площадь за текущую уборку, кв.м")
clean_time_seconds = Gauge(f"{METRIC_PREFIX}_clean_time_seconds", "Время текущей уборки, сек")
error_code = Gauge(f"{METRIC_PREFIX}_error_code", "Код ошибки (0 = нет ошибок)")
online = Gauge(f"{METRIC_PREFIX}_online", "Успешен ли последний опрос устройства (1/0)")
poll_duration_seconds = Gauge(f"{METRIC_PREFIX}_poll_duration_seconds", "Время последнего опроса устройства, сек")

# "Info"-метрика для строковых/enum состояний — удобно фильтровать и строить таблицы в Grafana
status_info = Info(f"{METRIC_PREFIX}_status", "Текущие строковые статусы пылесоса")

# DPS-коды согласно схеме устройства (см. m.life.device.ref.info.my.list)
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


# Пылесос при активной работе часто шлёт ЧАСТИЧНЫЕ обновления (только
# изменившиеся dps, например heartbeat), а не полный снимок каждый раз.
# Поэтому храним последние известные значения и обновляем только то,
# что реально пришло в конкретном ответе — остальное не затираем.
known_dps: dict = {}


def poll_once(d: tinytuya.Device) -> None:
    start = time.monotonic()
    result = d.status()
    duration = time.monotonic() - start
    poll_duration_seconds.set(duration)

    dps = result.get("dps") if isinstance(result, dict) else None

    if not dps:
        log.warning("Пустой или некорректный ответ от устройства: %s", result)
        online.set(0)
        return

    online.set(1)
    known_dps.update(dps)  # мержим частичный ответ поверх уже известного состояния

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
    log.info("Запуск hobot-exporter на порту %d, опрос каждые %d сек", EXPORTER_PORT, POLL_INTERVAL)
    start_http_server(EXPORTER_PORT)

    d = build_device()

    while True:
        try:
            poll_once(d)
        except Exception as e:
            log.error("Ошибка опроса устройства: %s", e)
            online.set(0)
            # На случай обрыва соединения — пересоздаём объект устройства
            try:
                d = build_device()
            except Exception as e2:
                log.error("Не удалось переподключиться: %s", e2)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
