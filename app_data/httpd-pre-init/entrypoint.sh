#!/bin/sh

while true; do python36 /opt/app-root/src/cron.py ratings /opt/app-root/src/odrs/static/ratings.json ; sleep 43200 ; done &
