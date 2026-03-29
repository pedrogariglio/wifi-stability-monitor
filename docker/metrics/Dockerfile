FROM alpine:3.19
ENV TZ=America/Argentina/Buenos_Aires

RUN apk add --no-cache bash wireless-tools iputils tzdata

COPY scripts/wifi-metrics.sh /usr/local/bin/wifi-metrics.sh
RUN chmod +x /usr/local/bin/wifi-metrics.sh

COPY docker/metrics/crontab /etc/crontabs/root

CMD ["crond", "-f", "-l", "2"]
