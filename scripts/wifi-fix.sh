#!/bin/bash

echo "=============================="
echo " REPARACIÓN WIFI - UBUNTU"
echo "=============================="
echo ""

echo "1) Reiniciando NetworkManager..."
sudo systemctl restart NetworkManager
sleep 3

echo "2) Apagando ahorro energético del WiFi..."
sudo iwconfig wlp6s0 power off
sleep 2

echo "3) Recargando driver iwlwifi..."
sudo modprobe -r iwlwifi
sleep 2
sudo modprobe iwlwifi
sleep 5

echo "=============================="
echo " Proceso terminado."
echo "=============================="

nmcli device status
