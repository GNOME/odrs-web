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

@reviews.route('/app/<appid>', methods=['GET', 'POST'])
def review_app(appid):
    """
    Either return details about an application or add a new review.
    """
    # get reviews
    if request.method == 'GET':
        try:
            db = ReviewsDatabase(os.environ)
            reviews = db.get_reviews_for_appid(appid)
        except CursorError as e:
            return error_internal(str(e))
    else:
        # add a new review
        item = json.loads(request.data)
        if not 'appid' in item:
            return error_internal('invalid data, expected appid')
        if not 'locale' in item:
            return error_internal('invalid data, expected locale')
        if not 'summary' in item:
            return error_internal('invalid data, expected summary')
        if not 'description' in item:
            return error_internal('invalid data, expected description')
        if not 'user_id' in item:
            return error_internal('invalid data, expected user_id')
        if not 'version' in item:
            return error_internal('invalid data, expected version')
        if not 'distro' in item:
            return error_internal('invalid data, expected distro')
        try:
            db = ReviewsDatabase(os.environ)
            db.add_app(item, _get_client_address())
        except CursorError as e:
            return json_error(str(e))
        reviews = [item]

    # return reviews
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
    # fixme: implement
    return json_success('deleted #%i' % dbid)

@reviews.route('/db/<int:dbid>/upvote')
def review_upvote(dbid):
    """
    Up-votes a review.
    """
    try:
        db = ReviewsDatabase(os.environ)
        reviews = db.vote(dbid, 1)
    except CursorError as e:
        return json_error(str(e))
    return json_success('incremented #%i' % dbid)

@reviews.route('/db/<int:dbid>/downvote')
def review_downvote(dbid):
    """
    Down-votes a review.
    """
    try:
        db = ReviewsDatabase(os.environ)
        reviews = db.vote(dbid, -1)
    except CursorError as e:
        return json_error(str(e))
    return json_success('decremented #%i' % dbid)
