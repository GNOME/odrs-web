#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

from flask import Blueprint, Response, request, flash, render_template
import json
import os

from database import ReviewsDatabase, CursorError

reviews = Blueprint('reviews', __name__, url_prefix='/reviews')

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
def review_add():
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

@reviews.route('/app/<appid>')
def review_app(appid):
    """
    Either return details about an application or add a new review.
    """
    # get reviews
    try:
        db = ReviewsDatabase(os.environ)
        reviews = db.get_reviews_for_appid(appid)
    except CursorError as e:
        return json_error(str(e))
    dat = json.dumps(reviews, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@reviews.route('/app/reviews')
def review_all():
    """
    Return all the reviews on the server as a JSON object.
    """
    try:
        db = ReviewsDatabase(os.environ)
        reviews = db.get_reviews()
    except CursorError as e:
        return json_error(str(e))
    dat = json.dumps(reviews, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@reviews.route('/db/<int:dbid>/delete')
def review_delete(dbid):
    """
    Delete a review.
    """
    # FIXME: implement
    return json_success('deleted #%i' % dbid)

@reviews.route('/db/<int:dbid>/upvote')
def review_upvote(dbid):
    """
    Up-votes a review.
    """
    #FIXME: read from POST
    user_id = 'testvalue2'
    try:
        db = ReviewsDatabase(os.environ)
        if db.has_voted(dbid, user_id):
            return json_error('already voted on this review')
        reviews = db.vote(dbid, 1, user_id)
    except CursorError as e:
        return json_error(str(e))
    return json_success('incremented #%i' % dbid)

@reviews.route('/db/<int:dbid>/downvote')
def review_downvote(dbid):
    """
    Down-votes a review.
    """
    #FIXME: read from POST
    user_id = 'testvalue2'
    try:
        db = ReviewsDatabase(os.environ)
        if db.has_voted(dbid, user_id):
            return json_error('already voted on this review')
        reviews = db.vote(dbid, -1, user_id)
    except CursorError as e:
        return json_error(str(e))
    return json_success('decremented #%i' % dbid)
