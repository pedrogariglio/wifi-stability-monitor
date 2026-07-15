## Debugging

- Si existe `nginx.conf` en el repo pero no se copia en la imagen (`Dockerfile`), el proxy no esta activo aunque "exista en papel".
- Para validar el camino real frontend -> backend, revisar juntos: `dashboard.html` (URL de fetch), `nginx.conf` (location `/api`) y `docker-compose.yml` (puertos publicados).
- Si el objetivo es que Nginx sea el unico entrypoint, no alcanza con proxy: hay que dejar el backend sin `ports` publicados y usar solo red interna (`expose`).
- Cuando el frontend usa rutas relativas (`/api/...`) se evita acoplar el cliente a un host/puerto del backend.
- Si `/api/kpis` responde 500 tras cerrar el bypass de backend, validar tipo del bind mount: `/var/log/wifi-metrics.csv` debe ser archivo regular (no directorio).
