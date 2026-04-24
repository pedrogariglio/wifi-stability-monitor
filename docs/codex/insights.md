# Insights tecnicos - wifi-stability-monitor (stack de observabilidad)

##Docker

- No usar `version` en Docker Compose v2
- Nunca usar `latest` en producción
- Usar `host-gateway` para acceder al host desde contenedores

---

##Prometheus

- Evitar targets con IP fija
- Usar `host.docker.internal` para exporters en host
- Un target DOWN puede ser problema de red, no del servicio

---

##Networking

- Las redes Docker custom no usan la misma gateway que el bridge default
- Nunca asumir que `172.17.0.1` es válido
