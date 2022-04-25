#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import sys
import os

sys.path.insert(0, os.environ['ODRS_HOME'])

def application(environ, start_response):
    for key in ['SQLALCHEMY_DATABASE_URI',
                'ODRS_REVIEWS_SECRET']:
        os.environ[key] = environ[key]
    from odrs import app as _application
    return _application(environ, start_response)
