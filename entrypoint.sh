#!/bin/sh

sed -i "s/replace_odrs_secret/${ODRS_REVIEWS_SECRET}/" /etc/httpd/sites.d/odrs.gnome.org.conf
sed -i "s/replace_odrs_username/${MYSQL_DB_USERNAME}/" /etc/httpd/sites.d/odrs.gnome.org.conf
sed -i "s/replace_odrs_password/${MYSQL_DB_PASSWORD}/" /etc/httpd/sites.d/odrs.gnome.org.conf
sed -i "s/replace_odrs_host/${MYSQL_DB_HOST}/" /etc/httpd/sites.d/odrs.gnome.org.conf

while true; do python /opt/app-root/src/cron.py ratings /opt/app-root/src/app/static/ratings.json ; sleep 43200 ; done &

exec /usr/bin/run-httpd
