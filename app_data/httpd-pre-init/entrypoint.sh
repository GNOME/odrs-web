#!/bin/sh

python36 /opt/app-root/src/app_data/wsgi-scripts/odrs-apache-setup.py ${HTTPD_CONFIGURATION_PATH}/odrs.gnome.org.conf

while true; do python36 /opt/app-root/src/cron.py ratings /opt/app-root/src/odrs/static/ratings.json ; sleep 43200 ; done &
