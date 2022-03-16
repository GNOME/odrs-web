#!/bin/sh

python3 /opt/app-root/src/wsgi-scripts/odrs-apache-setup.py ${HTTPD_CONFIGURATION_PATH}/odrs.gnome.org.conf

while true; do
  python3 /opt/app-root/src/cron.py ratings /opt/app-root/src/odrs/static/ratings.json
  sleep 43200
  cp /opt/app-root/src/odrs/static/ratings.json /opt/app-root/src/odrs/static/ratings.json.bak
  gzip /opt/app-root/src/odrs/static/ratings.json
  mv /opt/app-root/src/odrs/static/ratings.json.bak /opt/app-root/src/odrs/static/ratings.json
  brotli -k /opt/app-root/src/odrs/static/ratings.json
done &
while true; do python3 /opt/app-root/src/cron.py fsck ; sleep 43200 ; done &
