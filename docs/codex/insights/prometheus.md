##Prometheus

- Evitar targets con IP fija
- Usar `host.docker.internal` para exporters en host
- Un target DOWN puede ser problema de red, no del servicio
- Cuando Grafana se conecta a Prometheus, validar datasource en `Online` y probar query `up` en `Explore` antes de crear dashboards
