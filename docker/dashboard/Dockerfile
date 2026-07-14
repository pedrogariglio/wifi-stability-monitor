FROM nginx:1.25-alpine
RUN apk add --no-cache curl
COPY dashboard/dashboard.html /usr/share/nginx/html/index.html
COPY docker/dashboard/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
    