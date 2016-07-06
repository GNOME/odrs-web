#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import json
import os
import hashlib
import datetime
import calendar

from flask import Blueprint, Response, request, flash, render_template, escape, redirect, url_for
from flask.ext.login import login_required

from database import ReviewsDatabase, CursorError

reviews = Blueprint('reviews', __name__, url_prefix='/reviews')

def _get_user_key(user_hash, app_id):
    salt = os.environ['ODRS_REVIEWS_SECRET']
    key = 'invalid'
    try:
        key = hashlib.sha1(salt.encode('utf-8') +
                           user_hash.encode('utf-8') +
                           app_id.encode('utf-8')).hexdigest()
    except UnicodeEncodeError as e:
        print("invalid input: %s,%s: %s" % (user_hash, app_id, str(e)))
    return key

def _get_client_address():
    """ Gets user IP address """
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    else:
        return request.remote_addr

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

    # FIXME: include other locale quirks here
    return False

def _get_review_score(review, item):
    """ Gets a review score given certain parameters """
    score = 0
    if not _locale_is_compatible(review['locale'], item['locale']):
        score = score - 1000
    if review['version'] != item['version']:
        score = score + 100
    if review['distro'] != item['distro']:
        score = score + 100
    return score + (review['karma'] * 2)

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

@reviews.errorhandler(400)
def error_internal(msg=None, errcode=400):
    """ Error handler: Internal """
    flash("Internal error: %s" % msg)
    return render_template('error.html'), errcode

@reviews.errorhandler(401)
def error_permission_denied(msg=None):
    """ Error handler: Permission Denied """
    flash("Permission denied: %s" % msg)
    return render_template('error.html'), 401

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

def _check_str(val):
    """ Return with success if the summary and description """
    if val.find('<') != -1:
        return False
    if val.find('<') != -1:
        return False
    return True

@reviews.route('/api/submit', methods=['POST'])
def api_submit():
    """
    Submits a new review.
    """
    try:
        item = json.loads(request.data.decode('utf8'))
    except ValueError as e:
        return json_error(str(e))
    required_fields = ['app_id', 'locale', 'summary', 'description',
                       'user_hash', 'version', 'distro', 'rating',
                       'user_display']
    for key in required_fields:
        if not key in item:
            return json_error('invalid data, expected %s' % key)
        if item[key] is None:
            return json_error('missing data, expected %s' % key)

    # check format
    if not len(item['user_hash']) == 40:
        return json_error('the user_hash is invalid')

    # check fields for markup and length
    if not item['app_id'].endswith('.desktop'):
        return json_error('only applications can be reviewed at this time')
    if len(item['summary']) > 70:
        return json_error('summary is too long')
    if len(item['description']) > 3000:
        return json_error('description is too long')
    for key in ['summary', 'description']:
        if not _check_str(item[key]):
            return json_error('%s is not a valid string' % key)
    try:
        db = ReviewsDatabase(os.environ)

        # user has already reviewed
        if db.review_exists(item['app_id'], item['user_hash']):
            db.event_warn(_get_client_address(),
                          item['user_hash'],
                          item['app_id'],
                          "already reviewed")
            return json_error('already reviewed this app')

        # check user has not been banned
        user = db.user_get_by_id(item['user_hash'])
        if user and user['is_banned']:
            return json_error('account has been disabled due to abuse')

        # log and add review
        db.event_info(_get_client_address(),
                      item['user_hash'],
                      item['app_id'],
                      "reviewed")
        db.review_add(item, _get_client_address())
    except CursorError as e:
        return json_error(str(e))
    return json_success()

@reviews.route('/analytics')
@login_required
def html_analytics():
    """
    Show nice analytics graphs.
    """
    try:
        db = ReviewsDatabase(os.environ)
    except CursorError as e:
        return error_internal(str(e))

    # add days
    data_fetch = db.get_stats_by_interval(30, 1, 'fetching review')
    data_review = db.get_stats_by_interval(30, 1, 'reviewed')
    html = '<canvas id="reviewsChartDays" width="1200" height="400"></canvas>'
    html += '<script>'
    html += 'var ctx = document.getElementById("reviewsChartDays").getContext("2d");'
    html += 'var data = {'
    html += '    labels: %s,' % _get_chart_labels_days()[::-1]
    html += '    datasets: ['
    html += '        {'
    html += '            label: "Requests",'
    html += '            fillColor: "rgba(120,120,120,0.15)",'
    html += '            strokeColor: "rgba(120,120,120,0.15)",'
    html += '            pointColor: "rgba(120,120,120,0.20)",'
    html += '            pointStrokeColor: "#fff",'
    html += '            pointHighlightFill: "#fff",'
    html += '            pointHighlightStroke: "rgba(220,220,220,1)",'
    html += '            data: %s' % data_fetch[0][::-1]
    html += '        },'
    html += '        {'
    html += '            label: "Users",'
    html += '            fillColor: "rgba(20,120,220,0.2)",'
    html += '            strokeColor: "rgba(20,120,120,0.1)",'
    html += '            pointColor: "rgba(20,120,120,0.3)",'
    html += '            pointStrokeColor: "#fff",'
    html += '            pointHighlightFill: "#fff",'
    html += '            pointHighlightStroke: "rgba(220,220,220,1)",'
    html += '            data: %s' % data_fetch[1][::-1]
    html += '        },'
    html += '        {'
    html += '            label: "Submitted",'
    html += '            fillColor: "rgba(251,14,5,0.2)",'
    html += '            strokeColor: "rgba(151,14,5,0.1)",'
    html += '            pointColor: "rgba(151,14,5,0.3)",'
    html += '            pointStrokeColor: "#fff",'
    html += '            pointHighlightFill: "#fff",'
    html += '            pointHighlightStroke: "rgba(151,187,205,1)",'
    html += '            data: %s' % data_review[0][::-1]
    html += '        },'
    html += '    ]'
    html += '};'
    html += 'var myLineChartDays = new Chart(ctx).Line(data, null);'
    html += '</script>'
    html_perday = html

    # add months
    data_fetch = db.get_stats_by_interval(12, 30, 'fetching review')
    data_review = db.get_stats_by_interval(12, 30, 'reviewed')
    html = '<canvas id="reviewsChartMonths" width="1200" height="400"></canvas>'
    html += '<script>'
    html += 'var ctx = document.getElementById("reviewsChartMonths").getContext("2d");'
    html += 'var data = {'
    html += '    labels: %s,' % _get_chart_labels_months()[::-1]
    html += '    datasets: ['
    html += '        {'
    html += '            label: "Fetching",'
    html += '            fillColor: "rgba(120,120,120,0.15)",'
    html += '            strokeColor: "rgba(120,120,120,0.15)",'
    html += '            pointColor: "rgba(120,120,120,0.20)",'
    html += '            pointStrokeColor: "#fff",'
    html += '            pointHighlightFill: "#fff",'
    html += '            pointHighlightStroke: "rgba(220,220,220,1)",'
    html += '            data: %s' % data_fetch[0][::-1]
    html += '        },'
    html += '        {'
    html += '            label: "Users",'
    html += '            fillColor: "rgba(20,120,220,0.2)",'
    html += '            strokeColor: "rgba(20,120,120,0.1)",'
    html += '            pointColor: "rgba(20,120,120,0.3)",'
    html += '            pointStrokeColor: "#fff",'
    html += '            pointHighlightFill: "#fff",'
    html += '            pointHighlightStroke: "rgba(220,220,220,1)",'
    html += '            data: %s' % data_fetch[1][::-1]
    html += '        },'
    html += '        {'
    html += '            label: "Submitted",'
    html += '            fillColor: "rgba(251,14,5,0.2)",'
    html += '            strokeColor: "rgba(151,14,5,0.1)",'
    html += '            pointColor: "rgba(151,14,5,0.3)",'
    html += '            pointStrokeColor: "#fff",'
    html += '            pointHighlightFill: "#fff",'
    html += '            pointHighlightStroke: "rgba(151,187,205,1)",'
    html += '            data: %s' % data_review[0][::-1]
    html += '        },'
    html += '    ]'
    html += '};'
    html += 'var myLineChartMonths = new Chart(ctx).Line(data, null);'
    html += '</script>'
    html_permonth = html

    return render_template('analytics.html',
                           dyncontent_perday=html_perday,
                           dyncontent_permonth=html_permonth)

@reviews.route('/stats')
@login_required
def html_stats():
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

@reviews.route('/show/<review_id>')
def html_show(review_id):
    """
    Show a specific review as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
        item = db.review_get_for_id(review_id)
    except CursorError as e:
        return json_error(str(e))
    if not item:
        return json_error('no review with that ID')
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

@reviews.route('/modify/<review_id>', methods=['POST'])
@login_required
def html_modify(review_id):
    """ Change details about a review """
    try:
        db = ReviewsDatabase(os.environ)
        item = db.review_get_for_id(review_id)
    except CursorError as e:
        return json_error(str(e))
    if not item:
        return json_error('no review with that ID')
    item['distro'] = request.form['distro']
    item['locale'] = request.form['locale']
    item['user_display'] = request.form['user_display']
    item['description'] = request.form['description']
    item['summary'] = request.form['summary']
    item['version'] = request.form['version']
    db.review_modify(item)
    return redirect(url_for('.html_show', review_id=review_id))

@reviews.route('/all')
def html_all():
    """
    Return all the reviews on the server as HTML.
    """
    try:
        db = ReviewsDatabase(os.environ)
        reviews = db.review_get_all()
    except CursorError as e:
        return json_error(str(e))

    html = ''
    if len(reviews) == 0:
        return error_internal('No reviews available!')
    for item in reviews:
        html += '<tr>'
        tmp = _stringify_timestamp(item['date_created'])
        html += '<td class="history"><a href="show/%i">%s</a></td>' % (item['review_id'], int(item['review_id']))
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

@reviews.route('/api/app/<app_id>/<user_hash>')
@reviews.route('/api/app/<app_id>')
def api_app(app_id, user_hash=None):
    """
    Return details about an application.
    """
    try:
        db = ReviewsDatabase(os.environ)
        db.event_info(_get_client_address(), user_hash, app_id, "getting")
        reviews = db.review_get_for_app_id(app_id)
    except CursorError as e:
        return json_error(str(e))

    # add key if user_hash specified
    reviews_new = []
    for item in reviews:
        if user_hash:
            item['user_skey'] = _get_user_key(user_hash, item['app_id'])
        reviews_new.append(item)

    dat = json.dumps(reviews_new, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@reviews.route('/api/fetch', methods=['POST'])
def api_fetch():
    """
    Return details about an application.
    """
    try:
        item = json.loads(request.data.decode('utf8'))
    except ValueError as e:
        return json_error(str(e))
    for key in ['app_id', 'user_hash', 'locale', 'karma', 'distro', 'limit', 'version']:
        if not key in item:
            return json_error('invalid data, expected %s' % key)
        if item[key] is None:
            return json_error('missing data, expected %s' % key)

    # check format
    if not len(item['user_hash']) == 40:
        return json_error('the user_hash is invalid')

    try:
        db = ReviewsDatabase(os.environ)
        db.event_info(_get_client_address(), item['user_hash'], item['app_id'],
                      "fetching review")
        reviews = db.review_get_for_app_id(item['app_id'])
    except CursorError as e:
        return json_error(str(e))

    # if user does not exist then create
    user = db.user_get_by_id(item['user_hash'])
    if not user:
        db.user_add(item['user_hash'])

    # add score for review using secret sauce
    reviews_new = []
    for review in reviews:
        # limit to user specified karma
        if review['karma'] < item['karma']:
            continue
        review['user_skey'] = _get_user_key(item['user_hash'], review['app_id'])
        review['score'] = _get_review_score(review, item)

        # the UI can hide the vote buttons on reviews already voted on
        if db.vote_exists(review['review_id'], item['user_hash']):
            review['vote_id'] = 1

        reviews_new.append(review)

    # fake something so the user can get the user_skey
    if len(reviews_new) == 0:
        review = {}
        review['score'] = 0
        review['app_id'] = item['app_id']
        review['user_hash'] = item['user_hash']
        review['user_skey'] = _get_user_key(item['user_hash'], review['app_id'])
        reviews_new.append(review)

    # sort and cut to limit
    sorted(reviews_new, key=lambda item: item['score'])
    reviews_new = reviews_new[:item['limit']]

    dat = json.dumps(reviews_new, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@reviews.route('/api/all/<user_hash>')
@reviews.route('/api/all')
def api_all(user_hash=None):
    """
    Return all the reviews on the server as a JSON object.
    """
    try:
        db = ReviewsDatabase(os.environ)
        db.event_info(_get_client_address(), user_hash, None, "getting all reviews")
        reviews = db.review_get_all()
    except CursorError as e:
        return json_error(str(e))

    # the user specified a user_hash
    if user_hash:
        for item in reviews:
            item['user_skey'] = _get_user_key(user_hash, item['app_id'])

    dat = json.dumps(reviews, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@reviews.route('/api/moderate/<user_hash>')
def api_moderate(user_hash):
    """
    Return all the reviews on the server the user can moderate.
    """
    try:
        db = ReviewsDatabase(os.environ)
        db.event_info(_get_client_address(), user_hash, None, "getting moderatable reviews")
        reviews = db.review_get_all()
    except CursorError as e:
        return json_error(str(e))

    # only return reviews the user has not already voted on
    reviews_new = []
    for item in reviews:
        if not db.vote_exists(item['review_id'], user_hash):
            item['user_skey'] = _get_user_key(user_hash, item['app_id'])
            reviews_new.append(item)

    dat = json.dumps(reviews_new, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

def vote(val):
    """
    Up or downvote an existing review by @val karma points.
    """
    try:
        item = json.loads(request.data.decode('utf8'))
    except ValueError as e:
        return json_error(str(e))
    for key in ['review_id', 'app_id', 'user_hash', 'user_skey']:
        if not key in item:
            return json_error('invalid data, required %s' % key)
        if item[key] is None:
            return json_error('missing data, expected %s' % key)

    # check format
    if not len(item['user_hash']) == 40:
        return json_error('the user_hash is invalid')
    if not len(item['user_skey']) == 40:
        return json_error('the user_skey is invalid')

    # connect to database early
    try:
        db = ReviewsDatabase(os.environ)
    except CursorError as e:
        return json_error(str(e))

    if item['user_skey'] != _get_user_key(item['user_hash'], item['app_id']):
        db.event_warn(_get_client_address(), item['user_hash'], None,
                      "invalid user_skey of %s" % item['user_skey'])
        #print("expected user_skey of %s" % _get_user_key(item['user_hash'], item['app_id']))
        return json_error('invalid user_skey')
    try:

        # the user already has a review
        if db.vote_exists(item['review_id'], item['user_hash']):
            db.event_warn(_get_client_address(), item['user_hash'], item['app_id'],
                          "duplicate vote")
            return json_error('already voted on this app')

        # update the per-user karma
        user = db.user_get_by_id(item['user_hash'])
        if not user:
            db.user_add(item['user_hash'])
        else:

            # user is naughty
            if user['is_banned']:
                return json_error('account has been disabled due to abuse')

            # the user is too harsh
            if val < 0 and user['karma'] < -50:
                return json_error('all negative karma used up')
        db.user_update_karma(item['user_hash'], val)

        # add the vote to the database
        db.vote_add(item['review_id'], val, item['user_hash'])
        db.event_info(_get_client_address(), item['user_hash'], item['app_id'],
                      "voted %i on review" % val)

    except CursorError as e:
        return json_error(str(e))
    return json_success('voted #%i %i' % (item['review_id'], val))

@reviews.route('/api/upvote', methods=['POST'])
def api_upvote():
    """
    Upvote an existing review by one karma point.
    """
    return vote(1)

@reviews.route('/api/downvote', methods=['POST'])
def api_downvote():
    """
    Downvote an existing review by one karma point.
    """
    return vote(-1)

@reviews.route('/api/dismiss', methods=['POST'])
def api_dismiss():
    """
    Dismiss a review without rating it up or down.
    """
    return vote(0)

@reviews.route('/api/report', methods=['POST'])
def api_report():
    """
    Report a review for abuse.
    """
    return vote(-5)

@reviews.route('/api/remove', methods=['POST'])
def api_remove():
    """
    Remove a review.
    """
    try:
        item = json.loads(request.data.decode('utf8'))
    except ValueError as e:
        return json_error(str(e))
    for key in ['review_id', 'app_id', 'user_hash', 'user_skey']:
        if not key in item:
            return json_error('invalid data, required %s' % key)
        if item[key] is None:
            return json_error('missing data, expected %s' % key)

    # check format
    if not len(item['user_hash']) == 40:
        return json_error('the user_hash is invalid')
    if not len(item['user_skey']) == 40:
        return json_error('the user_skey is invalid')

    # connect to database early
    try:
        db = ReviewsDatabase(os.environ)
    except CursorError as e:
        return json_error(str(e))
    if item['user_skey'] != _get_user_key(item['user_hash'], item['app_id']):
        db.event_warn(_get_client_address(), item['user_hash'], None,
                      "invalid user_skey of %s" % item['user_skey'])
        return json_error('invalid user_skey')
    try:
        # the user already has a review
        db.review_remove(item['review_id'], item['user_hash'])
        db.event_info(_get_client_address(),
                      item['user_hash'],
                      item['app_id'],
                      "removed review")
    except CursorError as e:
        return json_error(str(e))
    return json_success('removed review #%i' % item['review_id'])

@reviews.route('/api/ratings/<app_id>')
def api_ratings(app_id):
    """
    Get the star ratings for a specific application.
    """
    try:
        db = ReviewsDatabase(os.environ)
        ratings = db.reviews_get_rating_for_app_id(app_id)
    except CursorError as e:
        return json_error(str(e))

    dat = json.dumps(ratings, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")
