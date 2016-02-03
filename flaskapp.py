#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import json

# http://reviews-xdgapp.rhcloud.com/api/reviews/gnome-terminal.desktop

# id: 80
# application: gnome-terminal.desktop
# locale: es
# date_created: 2016-01-01 00:00:00
# date_deleted: null
# summary: Awesome program
# description: Awesome program, but sometimes forgets my settings
# user_id: `sha1sum nonce + /etc/machine-id`
# user_ip: 192.168.1.1
# karma: -1
# version: 3.18.1
# distro: fedora

def main():
    apps = []

    app = {}
    app['id'] = 80
    app['application'] = 'gnome-terminal.desktop'
    apps.append(app)

    txt = json.dumps(apps, sort_keys=True, indent=4, separators=(',', ': '))
    print txt
    
    apps = json.loads(txt)
    print apps

if __name__ == "__main__":
    main()
