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

@admin.route('/popularity')
@login_required
def popularity():
    """
    Return the popularity page as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
    except CursorError as e:
        return error_internal(str(e))
    results1 = []
    for review in db.get_stats_fetch('fetching review'):
        results1.append((review[0].replace('.desktop', ''), review[1]))
    results2 = []
    for review in db.get_stats_fetch('reviewed'):
        results2.append((review[0].replace('.desktop', ''), review[1]))
    return render_template('popularity.html',
                           results1=results1,
                           results2=results2)

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
    results = []
    for item in stats:
        results.append((item, stats[item]))
    return render_template('stats.html', results=results)

@admin.context_processor
def utility_processor():
    def format_rating(rating):
        nr_stars = int(rating / 20)
        tmp = ''
        for i in range(0, nr_stars):
            tmp += '★'
        for i in range(0, 5 - nr_stars):
            tmp += '☆'
        return tmp

    def format_truncate(tmp, length):
        if len(tmp) <= length:
            return tmp
        return tmp[:length] + '…'

    def format_timestamp(tmp):
        if not tmp:
            return 'n/a'
        return datetime.datetime.fromtimestamp(tmp).strftime('%Y-%m-%d %H:%M:%S')

    return dict(format_rating=format_rating,
                format_truncate=format_truncate,
                format_timestamp=format_timestamp)

@admin.route('/review/<review_id>')
def review(review_id):
    """
    Show a specific review as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
        review = db.review_get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    return render_template('show.html', r=review)

@admin.route('/modify/<review_id>', methods=['POST'])
@login_required
def modify(review_id):
    """ Change details about a review """
    try:
        db = ReviewsDatabase(os.environ)
        review = db.review_get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    review.distro = request.form['distro']
    review.locale = request.form['locale']
    review.user_display = request.form['user_display']
    review.user_hash = request.form['user_hash']
    review.description = request.form['description']
    review.summary = request.form['summary']
    review.version = request.form['version']
    db.review_modify(review)
    return redirect(url_for('.review', review_id=review_id))

@admin.route('/unreport/<review_id>')
@login_required
def unreport(review_id):
    """ Unreport a perfectly valid review """
    try:
        db = ReviewsDatabase(os.environ)
        review = db.review_get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    review.reported = 0
    db.review_modify(review)
    return redirect(url_for('.review', review_id=review_id))

@admin.route('/unremove/<review_id>')
@login_required
def unremove(review_id):
    """ Unreport a perfectly valid review """
    try:
        db = ReviewsDatabase(os.environ)
        review = db.review_get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    review.date_deleted = 0
    db.review_modify(review)
    return redirect(url_for('.review', review_id=review_id))

@admin.route('/englishify/<review_id>')
@login_required
def englishify(review_id):
    """ Marks a review as writen in English """
    try:
        db = ReviewsDatabase(os.environ)
        review = db.review_get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    parts = review.locale.split('_')
    if len(parts) == 1:
        review.locale = 'en'
    else:
        review.locale = 'en_' + parts[1]
    db.review_modify(review)
    return redirect(url_for('.review', review_id=review_id))

@admin.route('/delete/<review_id>/force')
@login_required
def delete_force(review_id):
    """ Delete a review """
    try:
        db = ReviewsDatabase(os.environ)
        review = db.review_get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    db.review_delete(review)
    return redirect(url_for('.show_all'))

@admin.route('/delete/<review_id>')
@login_required
def delete(review_id):
    """ Ask for confirmation to delete a review """
    return render_template('delete.html', review_id=review_id)

@admin.route('/show_all')
def show_all():
    """
    Return all the reviews on the server as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
        reviews = db.review_get_all()
    except CursorError as e:
        return error_internal(str(e))
    return render_template('show-all.html', reviews=reviews)

@admin.route('/show_reported')
def show_reported():
    """
    Return all the reviews on the server as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
        reviews = db.review_get_all_reported()
    except CursorError as e:
        return error_internal(str(e))
    return render_template('show-all.html', reviews=reviews)

@admin.route('/user/<user_hash>')
def user(user_hash):
    """
    Return all the reviews from a user on the server as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
        reviews = db.review_get_all_for_user_hash(user_hash)
    except CursorError as e:
        return error_internal(str(e))
    return render_template('show-all.html', reviews=reviews)
