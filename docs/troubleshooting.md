# Troubleshooting

## Incidente: `/api/kpis` responde 500 despues de deploy

### Sintoma

- `curl http://localhost:8090/api/kpis` devuelve `500`.
- En logs del backend aparece:
  - `IsADirectoryError: [Errno 21] Is a directory: '/var/log/wifi-metrics.csv'`

### Causa raiz

El bind mount apunta a `/var/log/wifi-metrics.csv`, pero en host ese path existe como **directorio** en lugar de archivo CSV.

### Diagnostico

```bash
ls -ld /var/log/wifi-metrics.csv
docker compose logs backend --tail=100
```

### Solucion

```bash
sudo rm -rf /var/log/wifi-metrics.csv
sudo touch /var/log/wifi-metrics.csv
sudo chown "$USER":"$USER" /var/log/wifi-metrics.csv
docker compose restart metrics backend dashboard
```

### Verificacion

```bash
tail -5 /var/log/wifi-metrics.csv
curl -i http://localhost:8090/api/kpis
```

Esperado: CSV con datos y respuesta `200` en `/api/kpis`.
