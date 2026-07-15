# PROJECT_STATUS.md
**Proyecto:** wifi-stability-monitor  
**Fecha de última actualización:** 2026-07-14  
**Autor del handoff:** Pedro Gariglio  
**Estado general:** ✅ Etapa 1 de observabilidad completada y validada en producción

---

## 1. Objetivo del Proyecto

`wifi-stability-monitor` es un sistema de monitoreo de estabilidad de red WiFi que corre en un HomeLab sobre un HP EliteDesk mini PC con Ubuntu Server 24.04 LTS headless.

**Problema que resuelve:** detectar y registrar caídas, degradaciones y fluctuaciones de señal en la conexión WiFi doméstica, con alertas en tiempo real y métricas históricas consultables.

**Alcance actual:**
- Recolección de métricas WiFi cada 30 segundos (latencia, señal dBm, packet loss, estado)
- Almacenamiento en CSV para consulta histórica
- Dashboard web accesible remotamente vía Nginx
- Alertas por Telegram con lógica de cooldown
- Stack de observabilidad con Prometheus y Node Exporter (Etapa 1 completada)

**Alcance futuro:** visualización en Grafana, métricas custom de FastAPI, alertas desde Alertmanager, centralización de logs con Loki.

---

## 2. Arquitectura Actual

### Servicios Docker

| Servicio | Container | Imagen | Puerto externo | Red | Función |
|---|---|---|---|---|---|
| `backend` | `wifi-backend` | Build local | — (solo interno en `monitor-net`) | `monitor-net` | FastAPI — API REST y lógica de alertas Telegram |
| `dashboard` | `wifi-dashboard` | Build local | `8090:80` | `monitor-net` | Nginx — sirve el frontend del dashboard |
| `metrics` | `wifi-metrics` | Build local | — | `host` | Crond Alpine — recolecta métricas WiFi al CSV |
| `node-exporter` | `wifi-node-exporter` | `prom/node-exporter:v1.9.1` | — | `host` | Expone métricas del OS en `:9100/metrics` |
| `prometheus` | `wifi-prometheus` | `prom/prometheus:v3.11.2` | `9090:9090` | `monitor-net` | Scraping, almacenamiento y consulta de métricas |

### Redes Docker

```
monitor-net (bridge explícita):
  ├── wifi-backend        → accesible por nombre de servicio desde Prometheus
  ├── wifi-dashboard
  └── wifi-prometheus     → scrapea backend por nombre, node-exporter por IP del host

host:
  ├── wifi-metrics        → necesita acceso a wlp6s0 e ICMP reales
  └── wifi-node-exporter  → necesita ver interfaces, procesos y FS del host
```

**Gateway de `monitor-net`:** `172.18.0.1`  
**Gateway de `docker0` (bridge default):** `172.17.0.1`  
**Resolución de `host.docker.internal` dentro de Prometheus:** `172.17.0.1`

### Volúmenes

| Nombre | Tipo | Origen | Destino en container | Uso |
|---|---|---|---|---|
| `prometheus-data` | Named volume | Docker gestionado | `/prometheus` | Base de datos TSDB de Prometheus |
| — | Bind mount | `/var/log/wifi-metrics.csv` | `/var/log/wifi-metrics.csv` | CSV de métricas WiFi (compartido entre `metrics` y `backend`) |

### Flujo de datos

```
[wlp6s0 / ping 8.8.8.8]
        ↓
[wifi-metrics: crond cada 30s]
        ↓ escribe
[/var/log/wifi-metrics.csv]
        ↓ lee (ro)
[wifi-backend: FastAPI :8088]
        ↓ proxy interno `/api/*`
[wifi-dashboard: Nginx :80 → :8090]
        ↓ alertas
[Telegram Bot API]

[wifi-node-exporter :9100/metrics] ←── scrape cada 15s ──┐
[wifi-backend :8088/metrics]        ←── scrape cada 15s ──┤
[wifi-prometheus :9090/metrics]     ←── scrape cada 15s ──┘ (self)
        ↓
[wifi-prometheus TSDB — retención 15 días]
```

### Dependencias entre servicios

```
wifi-dashboard   → depends_on: wifi-backend
wifi-prometheus  → depends_on: wifi-backend, wifi-node-exporter
wifi-metrics     → independiente (host mode)
wifi-node-exporter → independiente (host mode)
```

---

## 3. Estado Actual

### Qué funciona y fue validado

| Componente | Estado | Validación |
|---|---|---|
| Recolección de métricas WiFi | ✅ Funcionando | CSV se actualiza cada 30s, healthcheck verifica timestamp |
| FastAPI backend | ✅ Funcionando | Healthcheck en `/health`, responde correctamente |
| Dashboard Nginx | ✅ Funcionando | Accesible remotamente desde Dell via `192.168.18.29:8090` |
| Alertas Telegram | ✅ Funcionando | Lógica de cooldown implementada |
| Prometheus | ✅ UP | Validado en `Status → Targets`, se monitorea a sí mismo |
| Node Exporter | ✅ UP | 1502 líneas de métricas validadas desde dentro del container |
| Red `monitor-net` | ✅ Funcionando | Creada y operativa |
| Volumen `prometheus-data` | ✅ Creado | Persistencia de TSDB activa |

### Qué está DOWN por diseño (esperado)

| Componente | Estado | Motivo |
|---|---|---|
| `fastapi-backend` scrape job | ⚠️ DOWN (404) | FastAPI no expone `/metrics` todavía — se resuelve en Etapa 3 |

### Problemas resueltos recientemente

- UFW bloqueaba tráfico desde containers bridge hacia host (puerto 9100)
- `host.docker.internal` no resolvía correctamente en Linux con red explícita
- Identidad Git y SSH no configuradas en la Dell workstation
- `nginx.conf` existía pero no estaba activo en la imagen del dashboard; ahora se copia en build y el frontend consume `/api/*` vía rutas relativas

---

## 4. Decisiones Técnicas Tomadas

### Docker Compose v2 sin campo `version`
El campo `version: "3.9"` está deprecado en Compose v2 y genera warnings. Se eliminó para mantener compatibilidad con versiones actuales del plugin.

### Red explícita `monitor-net` en lugar de la red default
La red default de Compose no permite referenciar servicios por nombre de forma predecible cuando se mezclan con servicios en `host` mode. `monitor-net` da control explícito sobre qué servicios se ven entre sí y permite inspeccionar la red con nombre descriptivo.

### `network_mode: host` para `metrics` y `node-exporter`
- `metrics`: necesita acceso a `wlp6s0` (interfaz WiFi real) para `iwconfig` y para que el ping salga por la interfaz que se está midiendo. En red bridge esa interfaz no existe.
- `node-exporter`: necesita leer `/proc`, `/sys` y el filesystem del host para métricas reales del OS. También necesita `pid: host` para métricas de procesos.

### `host.docker.internal` + `host-gateway` para scraping de Node Exporter
Hardcodear `172.17.0.1` era frágil porque esa es la gateway del bridge default (`docker0`), no de `monitor-net`. `host.docker.internal` con `extra_hosts: host-gateway` es portable y no depende de subnets asignadas dinámicamente.

> **Nota:** En Linux, `host-gateway` resuelve a la IP del bridge default (`172.17.0.1`), no a la gateway de redes explícitas. Esto es comportamiento esperado y documentado. Node Exporter en `host` mode escucha en todas las interfaces, por lo que `172.17.0.1:9100` es accesible.

### Reglas UFW explícitas para subnets Docker
UFW con política `deny (incoming)` bloquea silenciosamente el tráfico container → host. Se agregaron reglas para `172.17.0.0/16` y `172.18.0.0/16` hacia el puerto 9100. Criterio: cubrir ambas subnets para no depender de la asignación dinámica de Docker.

### Versionado explícito de imágenes Docker
`prom/prometheus:v3.11.2` y `prom/node-exporter:v1.9.1` en lugar de `:latest`. Evita cambios inesperados en `docker compose pull`. Cualquier actualización debe ser una decisión explícita registrada en el historial de git.

### Volumen nombrado para Prometheus en lugar de bind mount
Prometheus corre con usuario no-root dentro del container. Un bind mount (`./data:/prometheus`) genera problemas de permisos. Un volumen nombrado Docker los gestiona automáticamente.

### Retención TSDB de 15 días
Balance entre historia útil y uso de disco en un mini PC de HomeLab. Configurable via `--storage.tsdb.retention.time`.

### `.env.example` trackeado en git
`.env` real excluido por `.gitignore`. `.env.example` con variables vacías incluido con excepción explícita `!.env.example`. Permite reproducir el proyecto sin exponer secretos.

### Commits separados por responsabilidad
`prometheus.yml` (configuración de herramienta) y `docker-compose.yml` (infraestructura del stack) en commits distintos. Facilita bisect y lectura del historial.

---

## 5. Problemas Resueltos

| Problema | Causa raíz | Solución aplicada | Lección aprendida |
|---|---|---|---|
| Node Exporter DOWN: `context deadline exceeded` | UFW con política `deny` bloqueaba tráfico desde containers bridge hacia host | `sudo ufw allow from 172.17.0.0/16 to any port 9100` y `172.18.0.0/16` | Siempre agregar reglas UFW al definir servicios en `host` mode que deban ser alcanzados desde containers bridge |
| `host.docker.internal` apuntaba a IP incorrecta | En Linux, `host-gateway` resuelve al bridge default (`docker0`), no a redes explícitas | Confirmado que `172.17.0.1` es accesible porque Node Exporter escucha en todas las interfaces | `host-gateway` es correcto en Linux; el problema era UFW, no la resolución de nombre |
| `wget \| head -5` dejaba terminal colgada | `head` cierra el pipe después de 5 líneas; `wget` no maneja bien `SIGPIPE` en este contexto | Reemplazar por `wget -qO- ... \| wc -l` para verificar sin truncar el stream | Preferir `curl` o `wc -l` para verificaciones desde containers con wget |
| `172.17.0.1` hardcodeado en `prometheus.yml` | Asunción incorrecta de que la gateway de `monitor-net` sería la misma que `docker0` | Reemplazado por `host.docker.internal` con `extra_hosts: host-gateway` | Nunca hardcodear IPs de subnets Docker; usar nombres o palabras reservadas de Compose |
| Git commits fallaban en la Dell | Identidad de Git (`user.email`, `user.name`) no configurada globalmente | `git config --global user.email` y `user.name` | Configurar identidad Git es el primer paso en cualquier máquina nueva |
| `git push` fallaba con `Permission denied (publickey)` | Clave SSH de la Dell no estaba registrada en GitHub | Agregar `~/.ssh/id_ed25519.pub` en GitHub → Settings → SSH keys | Verificar `ssh -T git@github.com` antes de intentar push en máquina nueva |
| `version: "3.9"` deprecation warning | Campo obsoleto en Docker Compose v2 | Eliminado del `docker-compose.yml` | Compose v2 no requiere ni recomienda el campo `version` |
| Proxy Nginx de `/api` no operaba en runtime | `nginx.conf` no estaba incorporado a la imagen y el frontend llamaba directo a `:8088` | Copiar `nginx.conf` en `docker/dashboard/Dockerfile`, migrar frontend a rutas relativas `/api/*` y cerrar exposición host del backend (`expose: 8088` sin `ports`) | Un proxy no existe hasta que su config entra en la imagen y se retira el bypass directo al backend |

---

## 6. Estado del TODO

`TODO.md` está disponible en la raíz del proyecto y fue reconciliado con este estado el 2026-07-14 (último update del TODO: 2026-07-14).

### Completado
- Etapa 1 de observabilidad completada: Prometheus + Node Exporter integrados y validados
- Scrape jobs de Prometheus configurados y targets validados en `Status -> Targets`
- Red explícita `monitor-net`, volumen `prometheus-data` y versionado fijo de imágenes de infraestructura
- Reglas UFW para subnets Docker hacia puerto 9100 aplicadas y verificadas
- Stack base operativo: backend FastAPI, dashboard Nginx, collector de métricas WiFi y alertas Telegram con cooldown
- Nginx definido como punto de entrada del frontend y proxy interno hacia backend (`/api/*`)

### En progreso
- No hay tareas en progreso activas al último update del `TODO.md` (2026-04-24)

### Pendiente
- **Etapa 1 (pendientes residuales):**
  - Aprender queries básicas en PromQL
  - Agregar healthchecks para `node-exporter` y `prometheus`
- **Etapa 2:** Grafana — dashboards visuales sobre métricas de Prometheus
- **Etapa 3:** Métricas custom en FastAPI — exponer `/metrics` con `prometheus-client`
- **Etapa 4:** Alertmanager — alertas desde Prometheus (complementario al sistema Telegram actual)
- **Etapa 5:** Loki — centralización de logs del stack
- Migración de secretos a archivos bajo `./secrets/` en lugar de variables de entorno
- `chmod 600 .env` en el servidor
- Implementar `gitleaks` o pre-commit hook para detección de secretos

### Futuras mejoras identificadas
- DisplayPort dummy plug para resolver boot headless del HP EliteDesk (BIOS requiere display físico para POST)
- TP-Link TL-SG2008 JetStream Smart Switch para VLANs y SNMP v3
- Segundo nodo compute para cluster Proxmox
- UPS

---

## 7. Riesgos y Deuda Técnica

### Configuraciones frágiles

**Subnets Docker hardcodeadas en UFW**  
Las reglas UFW para `172.17.0.0/16` y `172.18.0.0/16` asumen que Docker mantendrá esas subnets. Si Docker reasigna rangos (poco probable pero posible), el tráfico volvería a bloquearse silenciosamente. Mitigación: documentado en guía de contingencia; verificar con `docker network inspect` si Prometheus vuelve a perder Node Exporter.

**`host.docker.internal` resuelve a `172.17.0.1` en Linux**  
Comportamiento dependiente de la implementación de Docker en Linux. No está garantizado entre versiones. Si cambia, Node Exporter quedará DOWN. Mitigación: monitorear en `Status → Targets` después de actualizaciones de Docker.

**Bind mount de `/var/log/wifi-metrics.csv`**  
El archivo existe en el host fuera del control de Docker. Si se borra o cambia de path, `backend` y `metrics` fallan. No hay backup automatizado del CSV.

### Dependencias críticas

- `wlp6s0`: el nombre de la interfaz WiFi está hardcodeado en `wifi-metrics.sh`. Si cambia (reasignación de kernel), el script falla silenciosamente — `iwconfig` no devuelve error, devuelve vacío.
- Token de Telegram en `.env`: si se rota el bot o se revoca el token, las alertas dejan de funcionar sin aviso en el stack.
- Boot headless del HP EliteDesk: requiere DisplayPort dummy plug para arrancar sin monitor físico. Sin él, el servidor no completa POST.

### Deuda técnica

| Item | Severidad | Descripción |
|---|---|---|
| Secretos como variables de entorno | Media | TELEGRAM_TOKEN visible en `docker inspect`. Migrar a archivos bajo `./secrets/` |
| Sin healthcheck en `node-exporter` y `prometheus` | Baja | `docker compose ps` no muestra estado de salud para estos servicios |
| `fastapi-backend` scrape job DOWN | Baja | Esperado hasta Etapa 3, pero genera ruido en la UI de Prometheus |
| Sin rotación de logs del CSV | Media | El CSV crece indefinidamente. Sin logrotate configurado puede llenar el disco en el largo plazo |
| Imágenes locales sin tag | Baja | Las imágenes buildeadas localmente (`wifi-backend`, `wifi-dashboard`, `wifi-metrics`) no tienen versión explícita |
| Bind mount CSV puede apuntar a directorio | Media | Si `/var/log/wifi-metrics.csv` es directorio en host, backend responde 500 (`IsADirectoryError`) hasta corregir el path |

---

## 8. Próximos Pasos Recomendados

### Próxima sesión
1. **PromQL básico** — aprender queries sobre métricas de Node Exporter ya disponibles: CPU, memoria, disco, red
2. **Healthchecks para Prometheus y Node Exporter** — completar paridad con los otros servicios

### Próximas 2 semanas
3. **Etapa 2: Grafana** — agregar servicio al `docker-compose.yml`, conectar a Prometheus como datasource, crear primer dashboard con métricas del OS
4. **Migración de secretos** — mover TELEGRAM_TOKEN y TELEGRAM_CHAT_ID a `./secrets/` con patrón `read_secret()` en FastAPI

### Largo plazo
5. **Etapa 3: FastAPI `/metrics`** — agregar `prometheus-client`, exponer métricas de requests, latencia y errores
6. **Etapa 4: Alertmanager** — alertas desde Prometheus como complemento al sistema Telegram actual
7. **Loki** — centralización de logs de todos los containers
8. **Hardware:** DisplayPort dummy plug → TP-Link SG2008 → Proxmox segundo nodo

---

## 9. Checklist de Retorno al Proyecto

Guía rápida para retomar el proyecto después de semanas sin tocarlo.

### Verificar que el servidor está accesible
```bash
# Desde la Dell
ssh minipc
```

### Verificar estado del stack
```bash
cd ~/wifi-stability-monitor
docker compose ps
```
Esperado: todos los containers en estado `Up` o `Up (healthy)`.

### Verificar que las métricas WiFi se están recolectando
```bash
tail -5 /var/log/wifi-metrics.csv
```
El timestamp de la última línea no debe tener más de 2 minutos de antigüedad.

### Verificar Prometheus
```bash
# Desde browser en la Dell
http://192.168.18.29:9090/targets
```
Esperado:
- `prometheus` → UP
- `node-exporter` → UP
- `fastapi-backend` → DOWN (404, esperado hasta Etapa 3)

### Verificar Node Exporter directamente
```bash
curl http://localhost:9100/metrics | head -5
```

### Verificar conectividad container → host
```bash
docker exec wifi-prometheus wget -qO- http://172.17.0.1:9100/metrics 2>&1 | wc -l
```
Esperado: número mayor a 400.

### Verificar reglas UFW
```bash
sudo ufw status verbose
```
Deben existir reglas para `172.17.0.0/16` y `172.18.0.0/16` hacia puerto `9100`.

### Si algo está DOWN: secuencia de diagnóstico
```bash
# 1. Ver logs del servicio
docker compose logs <servicio> --tail=50

# 2. Reiniciar servicio problemático
docker compose restart <servicio>

# 3. Si hay cambios en el repo
git pull
docker compose up -d

# 4. Si Node Exporter está DOWN
sudo ufw status verbose          # verificar reglas
docker network inspect wifi-stability-monitor_monitor-net | grep Gateway
docker exec wifi-prometheus cat /etc/hosts
```

### Sincronizar cambios desde la Dell al servidor
```bash
# En la Dell: commit y push
git add .
git commit -m "..."
git push

# En el servidor
git pull
docker compose up -d
```

---

## 10. Resumen Ejecutivo

`wifi-stability-monitor` es un stack Docker multi-container que monitorea la estabilidad WiFi de un HomeLab en un HP EliteDesk con Ubuntu Server 24.04 headless. El core del sistema — recolección de métricas cada 30 segundos, dashboard web, y alertas Telegram con cooldown — está completamente operativo. La Etapa 1 del stack de observabilidad fue completada en la sesión del 24/04/2026: Prometheus v3.11.2 y Node Exporter v1.9.1 están integrados, desplegados y validados en producción. El principal obstáculo encontrado fue UFW bloqueando el tráfico desde containers bridge hacia el host en el puerto 9100, resuelto con reglas explícitas para las subnets Docker. La arquitectura usa una red bridge explícita `monitor-net` para los servicios principales y `network_mode: host` para los collectors que necesitan acceso a interfaces de red reales. Los secretos se gestionan con `.env` excluido de git. Las imágenes de infraestructura tienen versiones fijadas. El acceso remoto desde la Dell workstation funciona via SSH y Nginx. El próximo paso inmediato es aprender PromQL sobre las métricas ya disponibles, seguido de Grafana como Etapa 2 de observabilidad. La deuda técnica más relevante es la migración de secretos de variables de entorno a archivos montados.
