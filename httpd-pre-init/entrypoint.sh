#!/bin/sh

sed -i "s/replace_odrs_secret/${ODRS_REVIEWS_SECRET}/" ${HTTPD_CONFIGURATION_PATH}/odrs.gnome.org.conf 
sed -i "s/replace_odrs_username/${MYSQL_DB_USERNAME}/" ${HTTPD_CONFIGURATION_PATH}/odrs.gnome.org.conf
sed -i "s/replace_odrs_password/${MYSQL_DB_PASSWORD}/" ${HTTPD_CONFIGURATION_PATH}/odrs.gnome.org.conf
sed -i "s/replace_odrs_host/${MYSQL_DB_HOST}/" ${HTTPD_CONFIGURATION_PATH}/odrs.gnome.org.conf

while true; do python /opt/app-root/src/cron.py ratings /opt/app-root/src/app/static/ratings.json ; sleep 43200 ; done &
