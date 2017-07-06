#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import sys
import os

sys.path.insert(0, os.path.join(os.environ['HOME'], 'html'))

def application(environ, start_response):
    for key in ['MYSQL_DB_HOST',
                'MYSQL_DB_USERNAME',
                'MYSQL_DB_PASSWORD',
                'ODRS_REVIEWS_SECRET']:
        os.environ[key] = environ[key]
    from flaskapp import app as _application
    return _application(environ, start_response)
