# wifi-stability-monitor

Sistema de monitoreo de conexión WiFi en Linux. Detecta problemas de conectividad, recopila métricas de estabilidad y las expone en un dashboard web con alertas automáticas por Telegram.

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

## Arquitectura (Docker-first)

```
Capa de recolección
└── container wifi-metrics (crond) → ejecuta wifi-metrics.sh cada 30 segundos

Capa de almacenamiento
└── /var/log/wifi-metrics.csv (host) → bind mount compartido entre collector y backend

Capa de aplicación
├── container wifi-backend (FastAPI :8088)   → KPIs, histórico y alertas Telegram
└── container wifi-dashboard (Nginx :8090)   → frontend operativo de visualización

Capa de observabilidad
├── container wifi-prometheus (:9090)        → scraping y TSDB (15 días)
└── container wifi-node-exporter (host mode) → métricas del OS host
```

---

## Estructura del repositorio

```
wifi-stability-monitor/
├── docker-compose.yml
├── config/
│   └── prometheus/prometheus.yml
├── scripts/
│   ├── init-server.sh          # Inicialización del servidor (ejecutar antes del primer deploy)
│   ├── wifi-watchdog.sh        # Watchdog de autorecuperación
│   ├── wifi-metrics.sh         # Recolección de métricas
│   ├── wifi-fix.sh             # Reparación manual de la interfaz
│   └── wifi-status.sh          # Diagnóstico del estado WiFi
├── dashboard/
│   ├── main.py                 # Backend FastAPI
│   └── dashboard.html          # Frontend web
├── docker/
│   ├── backend/
│   ├── dashboard/
│   └── metrics/
└── docs/
```

---

## Instalación y despliegue

### Requisitos

- Ubuntu Linux (probado en 22.04 / 24.04)
- Docker Engine + Docker Compose v2
- UFW activo (configuración restrictiva — ver nota más abajo)
- Interfaz WiFi activa en el host (por defecto `wlp6s0`)

### 1. Clonar el repositorio

```bash
git clone https://github.com/pedrogariglio/wifi-stability-monitor.git
cd wifi-stability-monitor
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# completar TELEGRAM_TOKEN y TELEGRAM_CHAT_ID
```

### 3. Inicializar el servidor

Este paso es obligatorio antes del primer `docker compose up`. Crea el archivo CSV con su cabecera y configura las reglas de UFW necesarias para que Prometheus alcance a Node Exporter.

```bash
chmod +x scripts/init-server.sh
sudo ./scripts/init-server.sh
```

> **Nota UFW:** el stack usa `network_mode: host` para Node Exporter y el collector de métricas. Con UFW en política `deny (incoming)`, el tráfico desde containers bridge hacia el host queda bloqueado por defecto. El script de inicialización agrega las reglas necesarias para las subnets Docker (`172.17.0.0/16` y `172.18.0.0/16`) hacia el puerto 9100.

### 4. Levantar el stack

```bash
docker compose up -d --build
```

### 5. Verificar estado

```bash
docker compose ps
docker compose logs metrics --tail=50
tail -5 /var/log/wifi-metrics.csv
```

### 6. Accesos

| Servicio | URL |
|---|---|
| Dashboard | `http://<host>:8090` |
| Prometheus | `http://<host>:9090` |
| Grafana | `http://<host>:3000` |
| Backend API (interno) | `http://backend:8088` (solo red Docker `monitor-net`) |

---

## Métricas recolectadas

El archivo `/var/log/wifi-metrics.csv` registra una línea cada 30 segundos:

| Campo | Descripción | Ejemplo |
|---|---|---|
| `timestamp` | Fecha y hora del registro | `2026-03-12 17:50:17` |
| `estado` | `conectado`, `degradado` o `desconectado` | `conectado` |
| `latencia_ms` | Latencia promedio al ping (ms) | `26` |
| `signal_dbm` | Potencia de señal WiFi (dBm) | `-56` |
| `packet_loss_pct` | Porcentaje de paquetes perdidos | `0` |
| `evento` | `ok`, `degradado` o `caida` | `ok` |

---

## KPIs y umbrales (dashboard operativo)

| KPI | Verde | Amarillo | Rojo |
|---|---|---|---|
| Latencia | < 50ms | 50–150ms | > 150ms |
| Señal WiFi | > -65 dBm | -65 a -75 dBm | < -75 dBm |
| Packet loss | 0% | 1–5% | > 5% |
| Uptime | > 99% | 95–99% | < 95% |

---

## Estado del proyecto

- [x] Stack Docker operativo (`metrics`, `backend`, `dashboard`, `prometheus`, `node-exporter`)
- [x] Recolección de métricas en CSV cada 30 segundos (latencia, señal, packet loss, estado)
- [x] Dashboard web operativo con KPIs y gráficos en tiempo real
- [x] Alertas automáticas por Telegram con cooldown
- [x] Proxy Nginx correctamente configurado (frontend → `/api` → backend)
- [x] Etapa 1 de observabilidad completada (Prometheus + Node Exporter)
- [~] Etapa 2: Grafana (servicio base desplegado, falta datasource y dashboards)
- [ ] Etapa 3: endpoint `/metrics` en FastAPI con `prometheus-client`
- [ ] Etapa 4: Alertmanager
- [ ] Etapa 5: Loki

---

## Hardware

| Componente | Detalle |
|---|---|
| Mini PC | HP EliteDesk (Intel Core i5 vPro) — Ubuntu Server 24.04 LTS headless |
| Interfaz WiFi | `wlp6s0` (driver `iwlwifi`) |
| Switch (próximamente) | TP-Link TL-SG2008 JetStream (managed, VLAN, SNMP v3) |
| Router | Router doméstico del proveedor de internet |

---

## Licencia

MIT
