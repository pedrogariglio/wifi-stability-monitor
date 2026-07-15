# Despliegue

## Modo principal

El proyecto se despliega con Docker Compose.  
El unico punto de entrada web del stack es Nginx (`dashboard`) en el puerto `8090`.

## Requisitos

- Docker Engine + Docker Compose v2
- Archivo `.env` basado en `.env.example`
- Host Linux con interfaz WiFi operativa

## Despliegue desde cero

```bash
git clone https://github.com/pedrogariglio/wifi-stability-monitor.git
cd wifi-stability-monitor
cp .env.example .env
docker compose up -d --build
```

## Verificaciones post-deploy

```bash
docker compose ps
curl -i http://localhost:8090/
curl -i http://localhost:8090/api/kpis
curl -i http://localhost:8088/api/kpis
```

Resultado esperado:

- `8090` responde el dashboard.
- `8090/api/*` responde via proxy Nginx hacia backend.
- `8088` no es accesible desde host (backend interno en `monitor-net`).

## Precondicion critica de datos

El path `/var/log/wifi-metrics.csv` debe ser un **archivo regular**, no un directorio.

Si es directorio, el backend falla en `/api/kpis` con error `IsADirectoryError` al leer CSV.
