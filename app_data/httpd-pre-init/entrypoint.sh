#!/bin/sh

sed -i "s/replace_odrs_secret/${ODRS_REVIEWS_SECRET}/" ${HTTPD_CONFIGURATION_PATH}/odrs.gnome.org.conf 
sed -i "s/replace_odrs_database_uri/${SQLALCHEMY_DATABASE_URI}/" ${HTTPD_CONFIGURATION_PATH}/odrs.gnome.org.conf

while true; do python36 /opt/app-root/src/cron.py ratings /opt/app-root/src/odrs/static/ratings.json ; sleep 43200 ; done &
