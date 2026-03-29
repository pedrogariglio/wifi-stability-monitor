FROM alpine:3.19

RUN apk add --no-cache bash wireless-tools iputils

COPY scripts/wifi-metrics.sh /usr/local/bin/wifi-metrics.sh
RUN chmod +x /usr/local/bin/wifi-metrics.sh

COPY docker/metrics/crontab /etc/crontabs/root

CMD ["crond", "-f", "-l", "2"]
