# Runbook Operativo

## 1) Levantar/actualizar stack

```bash
cd ~/wifi-stability-monitor
docker compose up -d --build
docker compose ps
```

## 2) Health checks operativos

```bash
# Frontend (entrypoint)
curl -i http://localhost:8090/

# API via Nginx (camino real de produccion)
curl -i http://localhost:8090/api/kpis

# Backend directo desde host (debe estar cerrado)
curl -i http://localhost:8088/api/kpis
```

Esperado:

- `8090` devuelve 200 para `/`.
- `8090/api/kpis` devuelve 200 cuando hay CSV valido.
- `8088` no responde desde host (backend interno).

## 3) Diagnostico rapido si `/api/kpis` da 500

```bash
docker compose logs backend --tail=100
docker compose logs dashboard --tail=100
```

Si aparece `IsADirectoryError: '/var/log/wifi-metrics.csv'`:

- revisar y corregir el tipo de path en host (ver `docs/troubleshooting.md`).
