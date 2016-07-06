#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import json
import os
import datetime
import calendar

from flask import Blueprint, Response, request, flash, render_template, redirect, url_for
from flask.ext.login import login_required

from database import ReviewsDatabase, CursorError

admin = Blueprint('admin', __name__, url_prefix='/admin')

def _get_chart_labels_months():
    """ Gets the chart labels """
    now = datetime.date.today()
    labels = []
    offset = 0
    for i in range(0, 12):
        if now.month - i == 0:
            offset = 1
        labels.append(calendar.month_name[now.month - i - offset])
    return labels

def _get_chart_labels_days():
    """ Gets the chart labels """
    now = datetime.date.today()
    labels = []
    for i in range(0, 30):
        then = now - datetime.timedelta(i)
        labels.append("%02i-%02i-%02i" % (then.year, then.month, then.day))
    return labels

@admin.errorhandler(400)
def error_internal(msg=None, errcode=400):
    """ Error handler: Internal """
    flash("Internal error: %s" % msg)
    return render_template('error.html'), errcode

@admin.errorhandler(401)
def error_permission_denied(msg=None):
    """ Error handler: Permission Denied """
    flash("Permission denied: %s" % msg)
    return render_template('error.html'), 401


@admin.route('/graph_month')
@login_required
def graph_month():
    """
    Show nice graph graphs.
    """
    try:
        db = ReviewsDatabase(os.environ)
    except CursorError as e:
        return error_internal(str(e))
    data_fetch = db.get_stats_by_interval(30, 1, 'fetching review')
    data_review = db.get_stats_by_interval(30, 1, 'reviewed')
    return render_template('graph-month.html',
                           labels=_get_chart_labels_days()[::-1],
                           data_requests=data_fetch[0][::-1],
                           data_users=data_fetch[1][::-1],
                           data_submitted=data_review[0][::-1])

@admin.route('/graph_year')
@login_required
def graph_year():
    """
    Show nice graph graphs.
    """
    try:
        db = ReviewsDatabase(os.environ)
    except CursorError as e:
        return error_internal(str(e))
    data_fetch = db.get_stats_by_interval(12, 30, 'fetching review')
    data_review = db.get_stats_by_interval(12, 30, 'reviewed')
    return render_template('graph-year.html',
                           labels=_get_chart_labels_months()[::-1],
                           data_requests=data_fetch[0][::-1],
                           data_users=data_fetch[1][::-1],
                           data_submitted=data_review[0][::-1])

@admin.route('/stats')
@login_required
def stats():
    """
    Return the statistics page as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
        stats = db.get_stats()
    except CursorError as e:
        return error_internal(str(e))

    # list each stat the database can report
    html = ''
    for item in stats:
        html += '<tr>'
        html += '<td class="history">%s</td>' % item
        html += '<td class="history">%s</td>' % stats[item]
        html += '</tr>\n'
    html += '</table>'

    # list apps by view popularity
    html += '<h1>Top Applications (Page Views)</h1>'
    html += '<ol>'
    for item in db.get_stats_fetch('fetching review'):
        html += '<li>%s [%i]</li>' % (item[0].replace('.desktop', ''), item[1])
    html += '</ol>'

    # list apps by review popularity
    html += '<h1>Top Applications (Reviews)</h1>'
    html += '<ol>'
    for item in db.get_stats_fetch('reviewed'):
        html += '<li>%s [%i]</li>' % (item[0].replace('.desktop', ''), item[1])
    html += '</ol>'

    return render_template('stats.html', dyncontent=html)

def _stringify_rating(rating):
    nr_stars = int(rating / 20)
    tmp = ''
    for i in range(0, nr_stars):
        tmp += '&#9733;'
    for i in range(0, 5 - nr_stars):
        tmp += '&#9734;'
    return tmp

def _string_truncate(tmp, length):
    if len(tmp) <= length:
        return tmp
    return tmp[:length] + '&hellip;'

def _stringify_timestamp(tmp):
    if not tmp:
        return 'n/a'
    return datetime.datetime.fromtimestamp(tmp).strftime('%Y-%m-%d %H:%M:%S')

@admin.route('/review/<review_id>')
def review(review_id):
    """
    Show a specific review as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
        item = db.review_get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not item:
        return error_internal('no review with that ID')
    return render_template('show.html',
                           review_id=item['review_id'],
                           date_created=_stringify_timestamp(item['date_created']),
                           app_id=item['app_id'],
                           locale=item['locale'],
                           summary=item['summary'],
                           description=item['description'],
                           version=item['version'],
                           distro=item['distro'],
                           karma=item['karma'],
                           user_hash=item['user_hash'],
                           user_display=item['user_display'],
                           rating=_stringify_rating(item['rating']),
                           date_deleted=_stringify_timestamp(item['date_deleted']))

@admin.route('/modify/<review_id>', methods=['POST'])
@login_required
def modify(review_id):
    """ Change details about a review """
    try:
        db = ReviewsDatabase(os.environ)
        item = db.review_get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not item:
        return error_internal('no review with that ID')
    item['distro'] = request.form['distro']
    item['locale'] = request.form['locale']
    item['user_display'] = request.form['user_display']
    item['description'] = request.form['description']
    item['summary'] = request.form['summary']
    item['version'] = request.form['version']
    db.review_modify(item)
    return redirect(url_for('.review', review_id=review_id))

@admin.route('/all')
def all():
    """
    Return all the admin on the server as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
        admin = db.review_get_all()
    except CursorError as e:
        return error_internal(str(e))

    html = ''
    if len(admin) == 0:
        return error_internal('No admin available!')
    for item in admin:
        html += '<tr>'
        tmp = _stringify_timestamp(item['date_created'])
        html += '<td class="history"><a href="review/%i">%s</a></td>' % (item['review_id'], int(item['review_id']))
        html += '<td class="history">%s</td>' % tmp
        html += '<td class="history">%s</td>' % _stringify_timestamp(item['date_deleted'])
        html += '<td class="history">%s</td>' % item['app_id'].replace('.desktop', '')
        html += '<td class="history">%s</td>' % item['version']
        html += '<td class="history">%s</td>' % _stringify_rating(item['rating'])
        html += '<td class="history">%s</td>' % item['karma']
        html += '<td class="history">%s</td>' % item['distro']
        html += '<td class="history">%s</td>' % _string_truncate(item['user_hash'], 8)
        html += '<td class="history">%s</td>' % item['locale']
        html += '<td class="history">%s</td>' % item['user_display']
        html += '<td class="history">%s</td>' % _string_truncate(item['summary'], 20)
        html += '<td class="history">%s</td>' % _string_truncate(item['description'], 40)
        html += '</tr>\n'
    html += '</table>'

    return render_template('all.html', dyncontent=html)
