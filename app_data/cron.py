#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# pylint: disable=singleton-comparison
#
# Copyright (C) 2015-2019 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import json
import sys
import datetime
import csv
import gzip

from lxml import etree as ET

from odrs import db

from odrs.models import Review, Taboo, Component
from odrs.util import _get_rating_for_app_id, _get_taboos_for_locale

def _auto_delete(days=31):

    since = datetime.datetime.now() - datetime.timedelta(days=days)
    reviews = db.session.query(Review).\
                    filter(Review.date_deleted != None).\
                    filter(Review.date_deleted < since).\
                    order_by(Review.date_created.asc()).\
                    all()
    if len(reviews) > 1000:
        print('too many reviews to delete: {}'.format(len(reviews)))
        return
    print('Deleting {} reviews...'.format(len(reviews)))
    for review in reviews:
        db.session.delete(review)
    db.session.commit()

def _regenerate_ratings(fn):
    item = {}

    app_ids = [res[0] for res in db.session.query(Component.app_id).\
                                    order_by(Component.app_id.asc()).all()]
    for app_id in app_ids:
        ratings = _get_rating_for_app_id(app_id, 2)
        if len(ratings) == 0:
            continue
        item[app_id] = ratings

    # dump to file
    with open(fn, 'w') as outfd:
        outfd.write(json.dumps(item, sort_keys=True, indent=4, separators=(',', ': ')))

def _taboo_check():

    # this is moderately expensive, so cache for each locale
    taboos = {}
    for review in db.session.query(Review).\
                    filter(Review.reported < 5).all():
        if review.locale not in taboos:
            taboos[review.locale] = _get_taboos_for_locale(review.locale)
        matched_taboos = review.matches_taboos(taboos[review.locale])
        if matched_taboos:
            for taboo in matched_taboos:
                print(review.review_id, review.locale, taboo.value)
            review.reported = 5
    db.session.commit()

def _appstream_import(fn):

    # get existing components
    app_ids = {}
    for component in db.session.query(Component).all():
        app_ids[component.app_id] = component

    # parse xml
    with gzip.open(fn, 'rb') as f:
        for component in ET.fromstring(f.read()).xpath('/components/component'):
            app_id = component.xpath('id')[0].text
            if app_id not in app_ids:
                continue
            children = []
            for provide in component.xpath('provides/id'):
                child_id = provide.text
                if child_id not in app_ids:
                    continue
                if app_ids[child_id].component_id_parent:
                    continue
                children.append(app_ids[child_id])
            if not children:
                continue
            parent = app_ids[app_id]
            for child in children:
                print('adding AppStream parent for {} -> {}'.format(child.app_id,
                                                                    parent.app_id))
                parent.adopt(child)
    db.session.commit()

def _taboo_import(fn):

    # get all the taboos in one database call
    taboos = {}
    for taboo in db.session.query(Taboo).all():
        key = taboo.locale + ':' + taboo.value
        taboos[key] = taboo

    # add any new ones
    with open(fn, newline='') as csvfile:
        for locale, values, description, severity in csv.reader(csvfile):
            locale = locale.strip()
            description = description.strip()
            for value in values.split('/'):
                value = value.strip()
                key = locale + ':' + value
                if key in taboos:
                    continue
                if value.find(' ') != -1:
                    print('Ignoring', locale, value)
                    continue
                if value.lower() != value:
                    print('Ignoring', locale, value)
                    continue
                taboo = Taboo(locale, value, description, severity=int(severity))
                taboos[key] = taboo
                print('Adding', locale, value)
                db.session.add(taboo)
    db.session.commit()

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Usage: %s ratings|auto-delete|taboo-check|taboo-import' % sys.argv[0])
        sys.exit(1)

    # create the ratings data
    if sys.argv[1] == 'ratings':
        if len(sys.argv) < 3:
            print('Usage: %s ratings filename' % sys.argv[0])
            sys.exit(1)
        _regenerate_ratings(sys.argv[2])
    elif sys.argv[1] == 'auto-delete':
        _auto_delete()
    elif sys.argv[1] == 'taboo-check':
        _taboo_check()
    elif sys.argv[1] == 'taboo-import':
        if len(sys.argv) < 3:
            print('Usage: %s taboo-import filename' % sys.argv[0])
            sys.exit(1)
        _taboo_import(sys.argv[2])
    elif sys.argv[1] == 'appstream-import':
        if len(sys.argv) < 3:
            print('Usage: %s taboo-import filename' % sys.argv[0])
            sys.exit(1)
        _appstream_import(sys.argv[2])
    else:
        print("cron mode %s not known" % sys.argv[1])
        sys.exit(1)

    # success
    sys.exit(0)
