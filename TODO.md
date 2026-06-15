# TODO — wifi-stability-monitor
**Última actualización:** 2026-04-24

---

## Stack de Observabilidad

### Etapa 1 — Prometheus + Node Exporter ✅
- [x] Crear `config/prometheus/prometheus.yml` con scrape jobs
- [x] Integrar `node-exporter` en `docker-compose.yml` con `network_mode: host` y `pid: host`
- [x] Integrar `prometheus` en `docker-compose.yml` con red `monitor-net`
- [x] Declarar red explícita `monitor-net`
- [x] Configurar `host.docker.internal` + `host-gateway` para scraping de Node Exporter
- [x] Agregar volumen nombrado `prometheus-data` para persistencia TSDB
- [x] Fijar versiones de imágenes (`prom/prometheus:v3.11.2`, `prom/node-exporter:v1.9.1`)
- [x] Configurar retención TSDB a 15 días
- [x] Agregar reglas UFW para subnets Docker (`172.17.0.0/16`, `172.18.0.0/16`) hacia puerto 9100
- [x] Validar targets en `Status → Targets` de la UI de Prometheus
- [x] Validar métricas de Node Exporter desde dentro del container
- [ ] Aprender queries básicas en PromQL sobre métricas disponibles
- [ ] Agregar healthchecks para `node-exporter` y `prometheus` en `docker-compose.yml`

### Etapa 2 — Grafana
- [ ] Agregar servicio `grafana` en `docker-compose.yml`
- [ ] Configurar Prometheus como datasource en Grafana
- [ ] Crear dashboard con métricas del OS (CPU, RAM, disco, red)
- [ ] Crear dashboard con métricas WiFi custom (cuando estén disponibles)
- [ ] Fijar versión de imagen de Grafana
- [ ] Agregar volumen nombrado para persistencia de dashboards
- [ ] Exponer Grafana via Nginx o acceso directo por puerto

### Etapa 3 — Métricas custom en FastAPI
- [ ] Agregar `prometheus-client` al `requirements.txt` del backend
- [ ] Implementar endpoint `/metrics` en `main.py`
- [ ] Exponer métricas de requests HTTP (contador por endpoint y status code)
- [ ] Exponer métricas de latencia (histograma)
- [ ] Exponer métricas de alertas Telegram enviadas
- [ ] Validar que el scrape job `fastapi-backend` pasa a UP en Prometheus

### Etapa 4 — Alertmanager
- [ ] Agregar servicio `alertmanager` en `docker-compose.yml`
- [ ] Crear `config/alertmanager/alertmanager.yml`
- [ ] Definir reglas de alertas en Prometheus (`alert.rules.yml`)
- [ ] Configurar receptor (Telegram o email)
- [ ] Evaluar convivencia con el sistema de alertas Telegram existente en FastAPI

### Etapa 5 — Loki (centralización de logs)
- [ ] Agregar servicio `loki` en `docker-compose.yml`
- [ ] Agregar `promtail` o `alloy` como agente de recolección de logs
- [ ] Configurar scraping de logs de todos los containers Docker
- [ ] Conectar Loki como datasource en Grafana

---

## Seguridad

- [ ] Migrar `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID` a archivos bajo `./secrets/`
- [ ] Actualizar `docker-compose.yml` para usar `secrets:` en lugar de `env_file` para el backend
- [ ] Actualizar `dashboard/main.py` para leer secretos con patrón `read_secret()` (archivo con fallback a env)
- [ ] Agregar `secrets/` a `.gitignore`
- [ ] Crear `secrets/*.txt.example` para documentar qué archivos se esperan
- [ ] Ejecutar `chmod 600 .env` en el servidor
- [ ] Evaluar implementar `gitleaks` o pre-commit hook para detección de secretos en commits

---

## Deuda Técnica

- [ ] Configurar `logrotate` para `/var/log/wifi-metrics.csv` (el archivo crece indefinidamente)
- [ ] Agregar tags de versión a las imágenes buildeadas localmente (`wifi-backend`, `wifi-dashboard`, `wifi-metrics`)
- [ ] Revisar si `network_mode: host` en `metrics` puede reemplazarse por `cap_add: NET_RAW` + red bridge (reducir superficie de ataque)
- [ ] Documentar el nombre de interfaz `wlp6s0` en un `.env` o variable de entorno para evitar hardcoding en `wifi-metrics.sh`

---

## Infraestructura y Hardware

### Inmediato
- [ ] Comprar DisplayPort dummy plug para resolver boot headless del HP EliteDesk (BIOS requiere display físico para POST)

### Corto plazo
- [ ] Instalar y configurar TP-Link TL-SG2008 JetStream Smart Switch (cuando llegue desde Australia)
- [ ] Configurar VLANs en el switch
- [ ] Configurar SNMP v3 en el switch para integración con Prometheus

### Mediano plazo
- [ ] Diagnosticar HDD Hitachi 1TB con `smartctl` antes de comprometer en enclosure
- [ ] Agregar segundo nodo compute para cluster Proxmox
- [ ] Configurar almacenamiento externo

### Largo plazo
- [ ] Instalar UPS
- [ ] Evaluar K3s para orquestación de containers

---

## Hoja de Ruta Completa

```
Etapa 1   Prometheus + Node Exporter    ✅ Completado (2026-04-24)
Etapa 2   Grafana                        ⬜ Pendiente
Etapa 3   FastAPI /metrics               ⬜ Pendiente
Etapa 4   Alertmanager                   ⬜ Pendiente
Etapa 5   Loki                           ⬜ Pendiente
```
