#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# pylint: disable=invalid-name,missing-docstring
#
# Copyright (C) 2015-2017 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 2

import datetime
import calendar
from math import ceil

from flask import abort, request, flash, render_template, redirect, url_for
from flask_login import login_required

from app import app, get_db
from .db import CursorError

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

class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

@app.errorhandler(400)
def error_internal(msg=None, errcode=400):
    """ Error handler: Internal """
    flash("Internal error: %s" % msg)
    return render_template('error.html'), errcode

@app.errorhandler(401)
def error_permission_denied(msg=None):
    """ Error handler: Permission Denied """
    flash("Permission denied: %s" % msg)
    return render_template('error.html'), 401


@app.route('/admin/graph_month')
@login_required
def graph_month():
    """
    Show nice graph graphs.
    """
    db = get_db()
    data_fetch = db.get_analytics_by_interval(30, 1)
    data_review = db.get_stats_by_interval(30, 1, 'reviewed')
    return render_template('graph-month.html',
                           labels=_get_chart_labels_days()[::-1],
                           data_requests=data_fetch[::-1],
                           data_submitted=data_review[::-1])

@app.route('/admin/graph_year')
@login_required
def graph_year():
    """
    Show nice graph graphs.
    """
    db = get_db()
    data_fetch = db.get_analytics_by_interval(12, 30)
    data_review = db.get_stats_by_interval(12, 30, 'reviewed')
    return render_template('graph-year.html',
                           labels=_get_chart_labels_months()[::-1],
                           data_requests=data_fetch[::-1],
                           data_submitted=data_review[::-1])

@app.route('/admin/stats')
@login_required
def show_stats():
    """
    Return the statistics page as HTML.
    """
    try:
        db = get_db()
        stats = db.get_stats()
    except CursorError as e:
        return error_internal(str(e))

    # stats
    results_stats = []
    for item in sorted(stats):
        results_stats.append((item, stats[item]))

    # popularity view
    results_viewed = []
    for review in db.get_analytics_fetch():
        results_viewed.append((review[0], review[1]))

    # popularity reviews
    results_submitted = []
    for review in db.get_stats_fetch('reviewed'):
        results_submitted.append((review[0], review[1]))
    return render_template('stats.html',
                           results_stats=results_stats,
                           results_viewed=results_viewed,
                           results_submitted=results_submitted)

@app.route('/admin/distros')
@login_required
def distros():
    """
    Return the statistics page as HTML.
    """
    try:
        db = get_db()
        stats = db.get_stats_distro(8)
    except CursorError as e:
        return error_internal(str(e))
    labels = []
    data = []
    for s in stats:
        name = s[0]
        for suffix in [' Linux', ' GNU/Linux', ' OS', ' Linux']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        labels.append(str(name))
        data.append(s[1])
    return render_template('distros.html', labels=labels, data=data)

@app.context_processor
def utility_processor():
    def format_rating(rating):
        nr_stars = int(rating / 20)
        tmp = ''
        for i in range(0, nr_stars):
            tmp += u'★'
        for i in range(0, 5 - nr_stars):
            tmp += u'☆'
        return tmp

    def format_truncate(tmp, length):
        if len(tmp) <= length:
            return tmp
        return tmp[:length] + u'…'

    def format_timestamp(tmp):
        if not tmp:
            return 'n/a'
        return datetime.datetime.fromtimestamp(tmp).strftime('%Y-%m-%d %H:%M:%S')

    def url_for_other_page(page):
        args = request.view_args.copy()
        args['page'] = page
        return url_for(request.endpoint, **args)

    return dict(format_rating=format_rating,
                format_truncate=format_truncate,
                format_timestamp=format_timestamp,
                url_for_other_page=url_for_other_page)

@app.route('/admin/review/<review_id>')
def admin_show_review(review_id):
    """
    Show a specific review as HTML.
    """
    try:
        db = get_db()
        review = db.reviews.get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    return render_template('show.html', r=review)

@app.route('/admin/modify/<review_id>', methods=['POST'])
@login_required
def admin_modify(review_id):
    """ Change details about a review """
    try:
        db = get_db()
        review = db.reviews.get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    review.distro = request.form['distro']
    review.locale = request.form['locale']
    if len(request.form['user_display']) == 0:
        review.user_display = None
    else:
        review.user_display = request.form['user_display']
    review.user_hash = request.form['user_hash']
    review.description = request.form['description']
    review.summary = request.form['summary']
    review.version = request.form['version']
    db.reviews.modify(review)
    return redirect(url_for('.admin_show_review', review_id=review_id))

@app.route('/admin/users.ban/<user_hash>')
@login_required
def admin_user_ban(user_hash):
    """ Change details about a review """
    try:
        db = get_db()
        db.users.ban(user_hash)
    except CursorError as e:
        return error_internal(str(e))
    return redirect(url_for('.admin_show_reported'))

@app.route('/admin/unreport/<review_id>')
@login_required
def admin_unreport(review_id):
    """ Unreport a perfectly valid review """
    try:
        db = get_db()
        review = db.reviews.get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    review.reported = 0
    db.reviews.modify(review)
    return redirect(url_for('.admin_show_review', review_id=review_id))

@app.route('/admin/unremove/<review_id>')
@login_required
def admin_unremove(review_id):
    """ Unreport a perfectly valid review """
    try:
        db = get_db()
        review = db.reviews.get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    review.date_deleted = 0
    db.reviews.modify(review)
    return redirect(url_for('.admin_show_review', review_id=review_id))

@app.route('/admin/englishify/<review_id>')
@login_required
def admin_englishify(review_id):
    """ Marks a review as writen in English """
    try:
        db = get_db()
        review = db.reviews.get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    parts = review.locale.split('_')
    if len(parts) == 1:
        review.locale = 'en'
    else:
        review.locale = 'en_' + parts[1]
    db.reviews.modify(review)
    return redirect(url_for('.admin_show_review', review_id=review_id))

@app.route('/admin/anonify/<review_id>')
@login_required
def admin_anonify(review_id):
    """ Removes the username from the review """
    try:
        db = get_db()
        review = db.reviews.get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    review.user_display = None
    db.reviews.modify(review)
    return redirect(url_for('.admin_show_review', review_id=review_id))

@app.route('/admin/delete/<review_id>/force')
@login_required
def admin_delete_force(review_id):
    """ Delete a review """
    try:
        db = get_db()
        review = db.reviews.get_for_id(review_id)
    except CursorError as e:
        return error_internal(str(e))
    if not review:
        return error_internal('no review with that ID')
    db.reviews.delete(review)
    return redirect(url_for('.admin_show_all'))

@app.route('/admin/delete/<review_id>')
@login_required
def admin_delete(review_id):
    """ Ask for confirmation to delete a review """
    return render_template('delete.html', review_id=review_id)

@app.route('/admin/show/all', defaults={'page': 1})
@app.route('/admin/show/all/page/<int:page>')
def admin_show_all(page):
    """
    Return all the reviews on the server as HTML.
    """
    try:
        db = get_db()
        reviews = db.reviews.get_all()
    except CursorError as e:
        return error_internal(str(e))
    if not reviews and page != 1:
        abort(404)
    reviews_per_page = 20
    pagination = Pagination(page, reviews_per_page, len(reviews))
    # FIXME: do this database side...
    reviews = reviews[(page-1) * reviews_per_page:page * reviews_per_page]
    return render_template('show-all.html',
                           pagination=pagination,
                           reviews=reviews)

@app.route('/admin/show/reported')
def admin_show_reported():
    """
    Return all the reported reviews on the server as HTML.
    """
    reviews_filtered = []
    try:
        db = get_db()
        reviews = db.reviews.get_all()
        for review in reviews:
            if review.reported > 0:
                reviews_filtered.append(review)
    except CursorError as e:
        return error_internal(str(e))
    return render_template('show-all.html', reviews=reviews_filtered)

@app.route('/admin/show/user/<user_hash>')
def admin_show_user(user_hash):
    """
    Return all the reviews from a user on the server as HTML.
    """
    reviews_filtered = []
    try:
        db = get_db()
        reviews = db.reviews.get_all()
        for review in reviews:
            if review.user_hash == user_hash:
                reviews_filtered.append(review)
    except CursorError as e:
        return error_internal(str(e))
    return render_template('show-all.html', reviews=reviews_filtered)

@app.route('/admin/show/app/<app_id>')
def admin_show_app(app_id):
    """
    Return all the reviews from a user on the server as HTML.
    """
    reviews_filtered = []
    try:
        db = get_db()
        reviews = db.reviews.get_all()
        for review in reviews:
            if review.app_id == app_id:
                reviews_filtered.append(review)
    except CursorError as e:
        return error_internal(str(e))
    return render_template('show-all.html', reviews=reviews_filtered)

@app.route('/admin/show/lang/<locale>')
def admin_show_lang(locale):
    """
    Return all the reviews from a user on the server as HTML.
    """
    reviews_filtered = []
    try:
        db = get_db()
        reviews = db.reviews.get_all()
        for review in reviews:
            if review.locale == locale:
                reviews_filtered.append(review)
    except CursorError as e:
        return error_internal(str(e))
    return render_template('show-all.html', reviews=reviews_filtered)

@app.route('/admin/users/all')
@login_required
def admin_users_all():
    """
    Return all the users as HTML.
    """
    try:
        db = get_db()
        users_awesome = db.users.get_by_karma(best=True)
        users_haters = db.users.get_by_karma(best=False)
    except CursorError as e:
        return error_internal(str(e))
    return render_template('users.html', users_awesome=users_awesome, users_haters=users_haters)
