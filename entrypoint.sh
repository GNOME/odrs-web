#!/bin/sh

sed -i "s/replace_odrs_secret/${ODRS_REVIEWS_SECRET}/" /etc/httpd/conf.d/odrs.gnome.org.conf
sed -i "s/replace_odrs_username/${MYSQL_DB_USERNAME}/" /etc/httpd/conf.d/odrs.gnome.org.conf
sed -i "s/replace_odrs_password/${MYSQL_DB_PASSWORD}/" /etc/httpd/conf.d/odrs.gnome.org.conf
sed -i "s/replace_odrs_host/${MYSQL_DB_HOST}/" /etc/httpd/conf.d/odrs.gnome.org.conf

exec /usr/bin/run-httpd
