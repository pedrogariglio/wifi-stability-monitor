#!/bin/bash

# ==============================================================================
# wifi-metrics.sh — Recolección de métricas de estabilidad WiFi
# Ubicación: /usr/local/bin/wifi-metrics.sh
# Ejecutado por: wifi-metrics.timer (cada 30 segundos)
# Salida: /var/log/wifi-metrics.csv
# ==============================================================================

IFACE="wlp6s0"
TARGET="8.8.8.8"
CSV="/var/log/wifi-metrics.csv"

# --- Crear cabecera si el archivo no existe ---
if [ ! -f "$CSV" ]; then
    echo "timestamp,estado,latencia_ms,signal_dbm,evento" >> "$CSV"
fi

# --- Timestamp ---
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# --- Señal WiFi (dBm) ---
SIGNAL=$(iwconfig "$IFACE" 2>/dev/null \
    | grep -i "Signal level" \
    | sed 's/.*Signal level=\([^ ]*\).*/\1/' \
    | tr -d 'dBm')

[ -z "$SIGNAL" ] && SIGNAL="-"

# --- Latencia (ping) y estado de conexión ---
PING_OUTPUT=$(ping -c 2 -W 3 "$TARGET" 2>/dev/null)

if echo "$PING_OUTPUT" | grep -q "2 received"; then
    ESTADO="conectado"
    LATENCIA=$(echo "$PING_OUTPUT" \
        | grep "rtt" \
        | sed 's/.*= [0-9.]*\/\([0-9.]*\)\/.*/\1/' \
        | cut -d'.' -f1)
    [ -z "$LATENCIA" ] && LATENCIA="-"
    EVENTO="ok"
else
    ESTADO="desconectado"
    LATENCIA="-"
    EVENTO="caida"
fi

# --- Escribir línea en CSV ---
echo "$TIMESTAMP,$ESTADO,$LATENCIA,$SIGNAL,$EVENTO" >> "$CSV"
