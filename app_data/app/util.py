#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import json

from flask import Response

def json_success(msg=None, errcode=200):
    """ Success handler: JSON output """
    item = {}
    item['success'] = True
    if msg:
        item['msg'] = msg
    dat = json.dumps(item, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=errcode, \
                    mimetype="application/json")

def json_error(msg=None, errcode=400):
    """ Error handler: JSON output """
    item = {}
    item['success'] = False
    if msg:
        item['msg'] = msg
    dat = json.dumps(item, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=errcode, \
                    mimetype="application/json")
