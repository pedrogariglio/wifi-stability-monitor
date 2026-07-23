# Insights tecnicos - wifi-stability-monitor (stack de observabilidad)

##Docker

- No usar `version` en Docker Compose v2
- Nunca usar `latest` en producción
- Usar `host-gateway` para acceder al host desde contenedores
- Al agregar un servicio nuevo, fijar versión de imagen y volumen nombrado desde el primer commit para mantener reproducibilidad
