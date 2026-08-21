#!/bin/sh
ENABLED=yes
PROCS=python3
ARGS="/opt/root/exporter.py"
PREARGS=""
DESC=$0
PATH=/opt/sbin:/opt/bin:/usr/sbin:/usr/bin:/sbin:/bin

# --- Настройки подключения к пылесосу и логированию ---
export HOBOT_DEVICE_ID="ЗАМЕНИ_НА_СВОЙ_devId"
export HOBOT_DEVICE_IP="ЗАМЕНИ_НА_IP_ПЫЛЕСОСА"
export HOBOT_LOCAL_KEY="ЗАМЕНИ_НА_СВОЙ_localKey"
export HOBOT_PROTOCOL_VERSION="3.3"
export HOBOT_POLL_INTERVAL="15"
export HOBOT_LOG_FILE="/opt/var/log/hobot-exporter.log"

. /opt/etc/init.d/rc.func
