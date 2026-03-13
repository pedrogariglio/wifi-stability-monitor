# wifi-stability-monitor

Sistema de monitoreo y autorecuperación de conexión WiFi en Linux. Detecta problemas de conectividad, intenta recuperarla automáticamente y recopila métricas de estabilidad para análisis y visualización.

Proyecto de aprendizaje en administración de sistemas Linux, automatización y observabilidad.

---

## El problema

La mini PC HP EliteDesk experimentaba problemas recurrentes con la conexión WiFi:

- Desconexiones intermitentes sin causa aparente
- El sistema quedaba marcado como "conectado" aunque no había acceso real a internet
- El reinicio del router no siempre era detectado por el sistema
- Velocidades significativamente menores que en otros dispositivos de la misma red

Se probaron soluciones manuales (reinicio de NetworkManager, desactivación del power saving del driver, ajustes en el módulo `iwlwifi`) antes de construir este sistema automatizado.

---

## Arquitectura

```
Capa de recolección
├── wifi-watchdog.sh      → detecta caídas y ejecuta recuperación automática
└── wifi-metrics.sh       → registra latencia, señal y estado cada 30 segundos

Capa de almacenamiento
└── /var/log/wifi-metrics.csv   → fuente única de verdad (histórico)

Capa de automatización
├── wifi-watchdog.service       → servicio continuo (Restart=always)
├── wifi-metrics.service        → ejecución puntual (Type=oneshot)
└── wifi-metrics.timer          → dispara wifi-metrics.service cada 30s

Capa de observabilidad (en desarrollo)
├── FastAPI                     → backend que lee el CSV y sirve JSON
├── Dashboard web               → KPIs, semáforos y gráficos en tiempo real (Plotly)
└── Telegram Bot                → alertas automáticas por umbral
```

---

## Estructura del repositorio

```
wifi-stability-monitor/
├── scripts/
│   ├── wifi-watchdog.sh        # Watchdog de autorecuperación
│   ├── wifi-metrics.sh         # Recolección de métricas
│   ├── wifi-fix.sh             # Reparación manual de la interfaz
│   └── wifi-status.sh          # Diagnóstico del estado WiFi
├── systemd/
│   ├── wifi-watchdog.service
│   ├── wifi-metrics.service
│   └── wifi-metrics.timer
├── logrotate/
│   └── wifi-watchdog           # Configuración de rotación de logs
├── analysis/                   # (próxima fase) Scripts Python de análisis
└── dashboard/                  # (próxima fase) FastAPI + Plotly
```

---

## Instalación

### Requisitos

- Ubuntu Linux (probado en 22.04 / 24.04)
- `iwconfig` (paquete `wireless-tools`)
- Interfaz WiFi activa (ajustar `IFACE` en los scripts si es distinta de `wlp6s0`)

### 1. Clonar el repositorio

```bash
git clone https://github.com/pedrogariglio/wifi-stability-monitor.git
cd wifi-stability-monitor
```

### 2. Instalar los scripts

```bash
sudo cp scripts/wifi-watchdog.sh /usr/local/bin/wifi-watchdog.sh
sudo cp scripts/wifi-metrics.sh /usr/local/bin/wifi-metrics.sh
sudo cp scripts/wifi-fix.sh /usr/local/bin/wifi-fix.sh
sudo cp scripts/wifi-status.sh /usr/local/bin/wifi-status.sh
sudo chmod +x /usr/local/bin/wifi-*.sh
```

### 3. Instalar los servicios systemd

```bash
sudo cp systemd/wifi-watchdog.service /etc/systemd/system/
sudo cp systemd/wifi-metrics.service /etc/systemd/system/
sudo cp systemd/wifi-metrics.timer /etc/systemd/system/

sudo systemctl daemon-reload

# Watchdog: servicio continuo
sudo systemctl enable wifi-watchdog.service
sudo systemctl start wifi-watchdog.service

# Métricas: activar el timer
sudo systemctl enable wifi-metrics.timer
sudo systemctl start wifi-metrics.timer
```

### 4. Configurar logrotate

```bash
sudo cp logrotate/wifi-watchdog /etc/logrotate.d/wifi-watchdog
```

### 5. Verificar que todo esté activo

```bash
systemctl status wifi-watchdog.service
systemctl status wifi-metrics.timer
cat /var/log/wifi-metrics.csv
```

---

## Métricas recolectadas

El archivo `/var/log/wifi-metrics.csv` registra una línea cada 30 segundos:

| Campo | Descripción | Ejemplo |
|---|---|---|
| `timestamp` | Fecha y hora del registro | `2026-03-12 17:50:17` |
| `estado` | `conectado` o `desconectado` | `conectado` |
| `latencia_ms` | Latencia promedio al ping (ms) | `26` |
| `signal_dbm` | Potencia de señal WiFi | `-56` |
| `evento` | `ok`, `caida` o `reconectado` | `ok` |

---

## KPIs y umbrales (dashboard en desarrollo)

| KPI | Verde | Amarillo | Rojo |
|---|---|---|---|
| Latencia | < 50ms | 50–150ms | > 150ms |
| Señal WiFi | > -65 dBm | -65 a -75 dBm | < -75 dBm |
| Packet loss | 0% | 1–5% | > 5% |
| Uptime | > 99% | 95–99% | < 95% |

---

## Estado del proyecto

- [x] Watchdog de autorecuperación con servicio systemd
- [x] Recolección de métricas en CSV cada 30 segundos
- [x] Rotación automática de logs con logrotate
- [ ] Ampliación de métricas: packet loss y throughput
- [ ] Script de análisis en Python (uptime, caídas por día, promedios)
- [ ] Dashboard web con FastAPI + Plotly (tiempo real)
- [ ] Alertas automáticas por Telegram

---

## Hardware utilizado

- **Mini PC:** HP EliteDesk (Intel Core i5 vPro) — Ubuntu Linux
- **Interfaz WiFi:** `wlp6s0` (driver `iwlwifi`)
- **Router:** router doméstico del proveedor de internet

---

## Aprendizajes aplicados

- Filesystem Hierarchy Standard (FHS) de Linux
- Gestión de servicios con `systemd` (`Type=simple`, `Type=oneshot`, timers)
- Rotación de logs con `logrotate`
- Scripting en bash para automatización del sistema
- Observabilidad: recolección y análisis de métricas de infraestructura

---

## Licencia

MIT
