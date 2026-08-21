"""
Диагностический скрипт для прямой проверки локального подключения к пылесосу
через tinytuya, в обход облака Tuya.

Использование:
    export HOBOT_DEVICE_ID=...
    export HOBOT_DEVICE_IP=...
    export HOBOT_LOCAL_KEY=...
    python3 check_vacuum.py

Не хранит секреты в самом файле — берёт из переменных окружения (те же,
что использует exporter.py). Значения можно взять из router/S99hobot-exporter
(если exporter развёрнут на роутере/другом отдельном устройстве).
"""
import os
import sys

import tinytuya

DEVICE_ID = os.environ.get("HOBOT_DEVICE_ID")
IP = os.environ.get("HOBOT_DEVICE_IP")
LOCAL_KEY = os.environ.get("HOBOT_LOCAL_KEY")
PROTOCOL_VERSION = float(os.environ.get("HOBOT_PROTOCOL_VERSION", "3.3"))

if not all([DEVICE_ID, IP, LOCAL_KEY]):
    print("Ошибка: заданы не все переменные окружения (HOBOT_DEVICE_ID, HOBOT_DEVICE_IP, HOBOT_LOCAL_KEY)")
    print("Подсказка: значения можно взять из ../router/S99hobot-exporter и задать export вручную")
    sys.exit(1)

d = tinytuya.Device(DEVICE_ID, IP, LOCAL_KEY)
d.set_version(PROTOCOL_VERSION)

status = d.status()
print(status)
