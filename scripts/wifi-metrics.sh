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
    echo "timestamp,estado,latencia_ms,signal_dbm,packet_loss_pct,evento" >> "$CSV"
fi

# --- Timestamp ---
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# --- Señal WiFi (dBm) ---
SIGNAL=$(iwconfig "$IFACE" 2>/dev/null \
    | grep -i "Signal level" \
    | sed 's/.*Signal level=\([^ ]*\).*/\1/' \
    | tr -d 'dBm')

[ -z "$SIGNAL" ] && SIGNAL="-"

# --- Ping: latencia, packet loss y estado ---
PING_OUTPUT=$(ping -c 2 -W 3 "$TARGET" 2>/dev/null)
RECEIVED=$(echo "$PING_OUTPUT" | grep -oE '[0-9]+ received' | grep -oE '[0-9]+')

# Packet loss
case "$RECEIVED" in
    2) PACKET_LOSS=0  ;;
    1) PACKET_LOSS=50 ;;
    *) PACKET_LOSS=100 ;;
esac

# Estado, latencia y evento
if [ "$RECEIVED" = "2" ]; then
    ESTADO="conectado"
    LATENCIA=$(echo "$PING_OUTPUT" \
        | grep "rtt" \
        | sed 's/.*= [0-9.]*\/\([0-9.]*\)\/.*/\1/' \
        | cut -d'.' -f1)
    [ -z "$LATENCIA" ] && LATENCIA="-"
    EVENTO="ok"
elif [ "$RECEIVED" = "1" ]; then
    ESTADO="degradado"
    LATENCIA=$(echo "$PING_OUTPUT" \
        | grep "rtt" \
        | sed 's/.*= [0-9.]*\/\([0-9.]*\)\/.*/\1/' \
        | cut -d'.' -f1)
    [ -z "$LATENCIA" ] && LATENCIA="-"
    EVENTO="degradado"
else
    ESTADO="desconectado"
    LATENCIA="-"
    EVENTO="caida"
fi

# --- Escribir línea en CSV ---
echo "$TIMESTAMP,$ESTADO,$LATENCIA,$SIGNAL,$PACKET_LOSS,$EVENTO" >> "$CSV"
