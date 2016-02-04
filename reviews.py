#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

from flask import Blueprint, Response, request, flash, render_template
import json
import os
import hashlib

from database import ReviewsDatabase, CursorError

reviews = Blueprint('reviews', __name__, url_prefix='/reviews')

def _get_user_key(user_id, app_id):
    #FIXME: this salt needs to be sekret
    salt = 'xdgapp'
    return hashlib.sha1(salt + user_id + app_id).hexdigest()

def _get_client_address():
    """ Gets user IP address """
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    else:
        return request.remote_addr

@reviews.errorhandler(401)
def error_permission_denied(msg=None):
    """ Error handler: Permission Denied """
    flash("Permission denied: %s" % msg)
    return render_template('error.html'), 401

@reviews.errorhandler(402)
def error_internal(msg=None, errcode=402):
    """ Error handler: Internal """
    flash("Internal error: %s" % msg)
    return render_template('error.html'), errcode

def json_error(msg=None, errcode=402):
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

@reviews.route('/app', methods=['POST'])
def add():
    """
    Either return details about an application or add a new review.
    """
    # add a new review
    try:
        item = json.loads(request.data)
    except ValueError as e:
        return json_error(str(e))
    required_fields = ['appid', 'locale', 'summary', 'description',
                       'user_id', 'version', 'distro']
    for key in required_fields:
        if not key in item:
            return json_error('invalid data, expected %s' % key)
    try:
        db = ReviewsDatabase(os.environ)
        if db.has_reviewed(item):
            return json_error('already reviewed this app')
        db.add_app(item, _get_client_address())
    except CursorError as e:
        return json_error(str(e))
    return json_success()

@reviews.route('/app/<appid>/<user_id>')
@reviews.route('/app/<appid>')
def get_app(appid, user_id=None):
    """
    Return details about an application.
    """
    # get reviews
    try:
        db = ReviewsDatabase(os.environ)
        reviews = db.get_reviews_for_appid(appid)
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

@reviews.route('/all/<user_id>')
@reviews.route('/all')
def get_all(user_id=None):
    """
    Return all the reviews on the server as a JSON object.
    """
    try:
        db = ReviewsDatabase(os.environ)
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

@reviews.route('/moderate/<user_id>')
def moderate(user_id):
    """
    Return all the reviews on the server the user can moderate.
    """
    try:
        db = ReviewsDatabase(os.environ)
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
    if item['user_key'] != _get_user_key(item['user_id'], item['appid']):
        print "expected user_key of %s", _get_user_key(item['user_id'], item['appid'])
        return json_error('invalid user_key')
    try:
        db = ReviewsDatabase(os.environ)
        if db.has_voted(item['dbid'], item['user_id']):
            return json_error('already reviewed this app')
        db.vote(item['dbid'], val, item['user_id'])
    except CursorError as e:
        return json_error(str(e))
    return json_success('voted #%i %i' % (item['dbid'], val))

@reviews.route('/upvote', methods=['POST'])
def upvote():
    """
    Upvote an existing review by one karma point.
    """
    return vote(1)

@reviews.route('/downvote', methods=['POST'])
def downvote():
    """
    Downvote an existing review by one karma point.
    """
    return vote(-1)
