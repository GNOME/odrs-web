#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import json
import hashlib

from sqlalchemy import text

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
                    mimetype='application/json')

def json_error(msg=None, errcode=400):
    """ Error handler: JSON output """
    item = {}
    item['success'] = False
    if msg:
        item['msg'] = msg
    dat = json.dumps(item, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=errcode, \
                    mimetype='application/json')

def _get_datestr_from_dt(when):
    return int('%04i%02i%02i' % (when.year, when.month, when.day))

def _get_user_key(user_hash, app_id):
    from odrs import app
    key = 'invalid'
    try:
        key = hashlib.sha1(app.secret_key.encode('utf-8') +
                           user_hash.encode('utf-8') +
                           app_id.encode('utf-8')).hexdigest()
    except UnicodeEncodeError as e:
        print('invalid input: %s,%s: %s' % (user_hash, app_id, str(e)))
    return key

def _eventlog_add(user_addr=None,
                  user_hash=None,
                  app_id=None,
                  message=None,
                  important=False):
    """ Adds a warning to the event log """
    from .models import Event
    from odrs import db
    db.session.add(Event(user_addr, user_hash, app_id, message, important))
    db.session.commit()

def _get_rating_for_app_id(app_id, min_total=1):
    """ Gets the ratings information for the application """
    from odrs import db
    stmt = text('SELECT COUNT(*) total,'
                '       SUM(rating = 0) star0,'
                '       SUM(rating = 20) star1,'
                '       SUM(rating = 40) star2,'
                '       SUM(rating = 60) star3,'
                '       SUM(rating = 80) star4,'
                '       SUM(rating = 100) star5 '
                'FROM reviews WHERE app_id=:app_id;')
    res = db.session.execute(stmt.bindparams(app_id=app_id)).fetchone() # pylint: disable=no-member
    if not res:
        return []
    item = {}
    item['total'] = res[0]
    if item['total'] < min_total:
        return []
    for i in range(6):
        if res[i + 1]:
            item['star%i' % i] = int(res[i + 1])
        else:
            item['star%i' % i] = 0
    return item

def _password_hash(value):
    """ Generate a legacy salted hash of the password string """
    salt = 'odrs%%%'
    return hashlib.sha1(salt.encode('utf-8') + value.encode('utf-8')).hexdigest()

def _sanitised_input(val):

    # remove trailing whitespace
    val = val.strip()

    # fix up style issues
    val = val.replace('!!!', '!')
    val = val.replace(':)', '')
    val = val.replace('  ', ' ')

    return val

def _sanitised_summary(val):
    val = _sanitised_input(val)
    if val.endswith('.'):
        val = val[:len(val)-1]
    return val

def _sanitised_description(val):
    return _sanitised_input(val)

def _sanitised_version(val):

    # remove epoch
    idx = val.find(':')
    if idx != -1:
        val = val[idx+1:]

    # remove distro addition
    idx = val.find('+')
    if idx != -1:
        val = val[:idx]
    idx = val.find('~')
    if idx != -1:
        val = val[:idx]

    return val

def _locale_is_compatible(l1, l2):
    """ Returns True if the locale is compatible """

    # trivial case
    if l1 == l2:
        return True

    # language code matches
    lang1 = l1.split('_')[0]
    lang2 = l2.split('_')[0]
    if lang1 == lang2:
        return True

    # LANG=C
    en_langs = ['C', 'en']
    if lang1 in en_langs and lang2 in en_langs:
        return True

    # perhaps include other locale quirks here?
    return False
