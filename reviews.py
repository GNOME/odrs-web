#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

from flask import Blueprint, Response, request, flash, render_template, escape
import json
import os
import hashlib

from database import ReviewsDatabase, CursorError

reviews = Blueprint('reviews', __name__, url_prefix='/reviews')

def _get_user_key(user_id, app_id):
    salt = os.environ['XDGAPP_REVIEWS_SECRET']
    return hashlib.sha1(salt + user_id + app_id).hexdigest()

def _get_client_address():
    """ Gets user IP address """
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    else:
        return request.remote_addr

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

@reviews.route('/')
def index():
    """
    The default page.
    """
    return render_template('index.html')

def _check_str(val):
    if val.find('<') != -1:
        return False
    if val.find('<') != -1:
        return False
    try:
        val.decode('utf-8')
    except UnicodeDecodeError:
        return False
    return True

@reviews.route('/api/app', methods=['POST'])
def api_add():
    """
    Either return details about an application or add a new review.
    """
    # add a new review
    try:
        item = json.loads(request.data)
    except ValueError as e:
        return json_error(str(e))
    required_fields = ['appid', 'locale', 'summary', 'description',
                       'user_id', 'version', 'distro', 'rating']
    for key in required_fields:
        if not key in item:
            return json_error('invalid data, expected %s' % key)

    # check fields for markup and length
    if len(item['summary']) > 40:
        return json_error('summary is too long')
    if len(item['description']) > 10240:
        return json_error('description is too long')
    for key in ['summary', 'description']:
        if not _check_str(item[key]):
            return json_error('%s is not a valid string' % key)

    try:
        db = ReviewsDatabase(os.environ)
        if db.has_reviewed(item):
            db.add_event(_get_client_address(), item['user_id'],
                         "already reviewed %s" % item['appid'])
            return json_error('already reviewed this app')
        db.add_app(item, _get_client_address())
    except CursorError as e:
        return json_error(str(e))
    return json_success()


@reviews.route('/api/eventlog')
def api_eventlog():
    """
    Return the event log as data.
    """
    # get events
    try:
        db = ReviewsDatabase(os.environ)
        events = db.get_events()
    except CursorError as e:
        return json_error(str(e))
    dat = json.dumps(events, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@reviews.route('/eventlog')
def html_eventlog():
    """
    Return the event log as HTML.
    """
    # get events
    try:
        db = ReviewsDatabase(os.environ)
        events = db.get_events()
    except CursorError as e:
        return internal_error(str(e))

    html = ''
    if len(events) == 0:
        return error_internal('No event log available!')
    for item in events:
        html += '<tr>'
        import datetime
        tmp = datetime.datetime.fromtimestamp(item['date_created']).strftime('%Y-%m-%d %H:%M:%S')
        html += '<td class="history">%s</td>' % tmp
        html += '<td class="history">%s</td>' % item['user_ip']
        html += '<td class="history">%s</td>' % item['user_id']
        html += '<td class="history">%s</td>' % escape(item['message'])
        html += '</tr>\n'
    html += '</table>'

    return render_template('eventlog.html', dyncontent=html)

@reviews.route('/api/app/<appid>/<user_id>')
@reviews.route('/api/app/<appid>')
def api_app(appid, user_id=None):
    """
    Return details about an application.
    """
    # get reviews
    try:
        db = ReviewsDatabase(os.environ)
        db.add_event(_get_client_address(), user_id,
                     "getting reviews for %s" % appid)
        reviews = db.get_reviews_for_appid(appid)
    except CursorError as e:
        return json_error(str(e))

    # ignore reviews created by the user
    reviews_new = []
    for item in reviews:
        if user_id:
            if user_id == item['user_id']:
                continue
            item['user_key'] = _get_user_key(user_id, item['appid'])
        reviews_new.append(item)

    dat = json.dumps(reviews_new, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@reviews.route('/api/all/<user_id>')
@reviews.route('/api/all')
def api_all(user_id=None):
    """
    Return all the reviews on the server as a JSON object.
    """
    try:
        db = ReviewsDatabase(os.environ)
        db.add_event(_get_client_address(), user_id, "getting all reviews")
        reviews = db.get_reviews()
    except CursorError as e:
        return json_error(str(e))

    # the user specified a user_id
    if user_id:
        for item in reviews:
            item['user_key'] = _get_user_key(user_id, item['appid'])

    dat = json.dumps(reviews, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@reviews.route('/api/moderate/<user_id>')
def api_moderate(user_id):
    """
    Return all the reviews on the server the user can moderate.
    """
    try:
        db = ReviewsDatabase(os.environ)
        db.add_event(_get_client_address(), user_id, "getting moderatable list")
        reviews = db.get_reviews()
    except CursorError as e:
        return json_error(str(e))

    # only return reviews the user has not already voted on
    reviews_new = []
    for item in reviews:
        if not db.has_voted(item['dbid'], user_id):
            item['user_key'] = _get_user_key(user_id, item['appid'])
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
        item = json.loads(request.data)
    except ValueError as e:
        return json_error(str(e))
    required_fields = ['dbid', 'appid', 'user_id', 'user_key']
    for key in required_fields:
        if not key in item:
            return json_error('invalid data, required %s' % key)

    # connect to database early
    try:
        db = ReviewsDatabase(os.environ)
    except CursorError as e:
        return json_error(str(e))

    if item['user_key'] != _get_user_key(item['user_id'], item['appid']):
        db.add_event(_get_client_address(), item['user_id'],
                     "invalid user_key of %s" % item['user_key'])
        #print "expected user_key of %s" % _get_user_key(item['user_id'], item['appid'])
        return json_error('invalid user_key')
    try:
        if db.has_voted(item['dbid'], item['user_id']):
            db.add_event(_get_client_address(), item['user_id'],
                         "attempted duplicate vote")
            return json_error('already reviewed this app')
        db.vote(item['dbid'], val, item['user_id'])
        db.add_event(_get_client_address(), item['user_id'],
                     "voted %i on %s" % (val, item['appid']))
    except CursorError as e:
        return json_error(str(e))
    return json_success('voted #%i %i' % (item['dbid'], val))

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

@reviews.route('/api/ratings/<appid>')
def api_ratings(appid):
    """
    Get the star ratings for a specific application.
    """
    try:
        db = ReviewsDatabase(os.environ)
        db.add_event(_get_client_address(), None,
                     "getting ratings for %s" % appid)
        ratings = db.get_ratings(appid)
    except CursorError as e:
        return json_error(str(e))

    dat = json.dumps(ratings, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")
