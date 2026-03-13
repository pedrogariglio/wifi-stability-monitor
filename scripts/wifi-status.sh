#!/bin/bash

echo "=============================="
echo " ESTADO WIFI"
echo "=============================="

nmcli device status
echo ""

echo "Potencia WiFi:"
iwconfig wlp6s0 | grep -i power
echo ""

echo "Driver cargado:"
lsmod | grep iwlwifi
echo ""

echo "Últimos errores relevantes:"
dmesg | grep iwlwifi | tail -n 5
