# Runbook Operativo

## 1) Levantar/actualizar stack

```bash
cd ~/wifi-stability-monitor
docker compose up -d --build
docker compose ps
```

## 2) Health checks operativos

Desde el servidor (CLI local):

```bash
# Frontend (entrypoint)
curl -i http://localhost:8090/

# API via Nginx (camino real de produccion)
curl -i http://localhost:8090/api/kpis

# Backend directo desde host (debe estar cerrado)
curl -i http://localhost:8088/api/kpis

# Grafana (Etapa 2)
curl -i http://localhost:3000/
```

Desde workstation (browser):

- Dashboard: `http://192.168.18.29:8090/`
- Grafana: `http://192.168.18.29:3000/`
- Prometheus: `http://192.168.18.29:9090/`

Esperado:

- `8090` devuelve 200 para `/`.
- `8090/api/kpis` devuelve 200 cuando hay CSV valido.
- `8088` no responde desde host (backend interno).
- `3000` responde la UI de Grafana.

## 3) Diagnostico rapido si `/api/kpis` da 500

```bash
docker compose logs backend --tail=100
docker compose logs dashboard --tail=100
```

Si aparece `IsADirectoryError: '/var/log/wifi-metrics.csv'`:

- revisar y corregir el tipo de path en host (ver `docs/troubleshooting.md`).

## 4) Verificar datasource de Grafana

Checklist:

- Abrir `http://192.168.18.29:3000/`
- Ir a `Connections -> Data sources`
- Confirmar `Prometheus` en estado `Online`
- Ejecutar una prueba simple en `Explore`:
  - consulta: `up`
  - esperado: series con valor `1` para targets saludables
