#!/bin/sh

python3 /opt/app-root/src/wsgi-scripts/odrs-apache-setup.py ${HTTPD_CONFIGURATION_PATH}/odrs.gnome.org.conf

while true; do
  python3 /opt/app-root/src/cron.py ratings /opt/app-root/src/odrs/static/ratings.json
  sleep 43200
  gzip -k /opt/app-root/src/odrs/static/ratings.json
  brotli -k /opt/app-root/src/odrs/static/ratings.json
done &
while true; do python3 /opt/app-root/src/cron.py fsck ; sleep 43200 ; done &
