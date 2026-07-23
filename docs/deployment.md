# Despliegue

## Modo principal

El proyecto se despliega con Docker Compose.  
El punto de entrada del frontend y la API del dashboard es Nginx (`dashboard`) en el puerto `8090`.  
Grafana se expone en forma directa por el puerto `3000` durante la Etapa 2.

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

Desde el servidor (CLI local):

```bash
docker compose ps
curl -i http://localhost:8090/
curl -i http://localhost:8090/api/kpis
curl -i http://localhost:8088/api/kpis
curl -i http://localhost:3000/
```

Desde workstation (browser):

- Dashboard: `http://192.168.18.29:8090/`
- Grafana: `http://192.168.18.29:3000/`
- Prometheus: `http://192.168.18.29:9090/`

Resultado esperado:

- `8090` responde el dashboard.
- `8090/api/*` responde via proxy Nginx hacia backend.
- `8088` no es accesible desde host (backend interno en `monitor-net`).
- `3000` responde la UI de Grafana.

## Verificacion del datasource en Grafana

Desde la UI de Grafana:

1. Ingresar a `http://192.168.18.29:3000/`
2. Ir a `Connections -> Data sources`
3. Validar que `Prometheus` figure en estado `Online`

## Precondicion critica de datos

El path `/var/log/wifi-metrics.csv` debe ser un **archivo regular**, no un directorio.

Si es directorio, el backend falla en `/api/kpis` con error `IsADirectoryError` al leer CSV.
