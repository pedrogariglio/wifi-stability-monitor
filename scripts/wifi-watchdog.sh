#!/bin/bash

LOG="/var/log/wifi-watchdog.log"
TARGET="8.8.8.8"
INTERVAL=15

echo "===============================" >> "$LOG"
echo "$(date) - Watchdog iniciado" >> "$LOG"
echo "===============================" >> "$LOG"

while true; do
    if ping -c 2 -W 3 $TARGET > /dev/null; then
        echo "$(date) - OK - Internet activo" >> "$LOG"
    else
        echo "$(date) - ERROR - Sin conectividad. Ejecutando reparación..." >> "$LOG"
        /home/pedrogariglio/scripts/wifi-fix.sh >> "$LOG" 2>&1
        echo "$(date) - Reparación ejecutada" >> "$LOG"
    fi
    sleep $INTERVAL
done
