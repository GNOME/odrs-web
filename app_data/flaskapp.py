#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2017 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

from app import app

if __name__ == '__main__':
    app.debug = True
    app.run()
