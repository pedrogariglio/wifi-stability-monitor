#!/bin/bash
# ==============================================================================
# init-server.sh — Inicialización del servidor antes del primer docker compose up
# Ejecutar una sola vez en cada servidor nuevo donde se despliegue el stack.
# ==============================================================================

set -e

echo "==> Creando /var/log/wifi-metrics.csv..."
sudo touch /var/log/wifi-metrics.csv

echo "==> Escribiendo cabecera del CSV..."
if ! head -1 /var/log/wifi-metrics.csv | grep -q "timestamp"; then
    echo "timestamp,estado,latencia_ms,signal_dbm,packet_loss_pct,evento" | sudo tee /var/log/wifi-metrics.csv > /dev/null
fi

echo "==> Ajustando permisos..."
sudo chmod 666 /var/log/wifi-metrics.csv

echo "==> Configurando reglas UFW para subnets Docker (Node Exporter)..."
sudo ufw allow from 172.17.0.0/16 to any port 9100 comment "prometheus -> node-exporter"
sudo ufw allow from 172.18.0.0/16 to any port 9100 comment "prometheus -> node-exporter (monitor-net)"
sudo ufw reload

echo ""
echo "✓ Inicialización completa. Podés ejecutar: docker compose up -d"
