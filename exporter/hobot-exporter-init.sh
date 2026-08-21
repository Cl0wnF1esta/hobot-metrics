#!/bin/sh
ENABLED=yes
PROCS=python3
ARGS="/opt/root/exporter.py"
PREARGS=""
DESC=$0
PATH=/opt/sbin:/opt/bin:/usr/sbin:/usr/bin:/sbin:/bin

# --- Device connection and logging settings ---
export HOBOT_DEVICE_ID="Replace_with_your_devId"
export HOBOT_DEVICE_IP="Replace_with_IP_device"
export HOBOT_LOCAL_KEY="Replace_with_localKey"
export HOBOT_PROTOCOL_VERSION="3.3"
export HOBOT_POLL_INTERVAL="15"
export HOBOT_LOG_FILE="/opt/var/log/hobot-exporter.log"

. /opt/etc/init.d/rc.func
