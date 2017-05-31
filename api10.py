#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import json
import os
import hashlib
import math

from flask import Blueprint, Response, request

from database import ReviewsDatabase, CursorError
from review import OdrsReview

api = Blueprint('api10', __name__, url_prefix='/')

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
    ku = review.karma_up
    kd = review.karma_down

    # hardcode some penalties
    if review.version != item['version']:
        kd = kd + 1
    if review.distro != item['distro']:
        kd = kd + 1

    # algorithm from http://www.evanmiller.org/how-not-to-sort-by-average-rating.html
    wilson = 0
    if ku > 0 or kd > 0:
        wilson = ((ku + 1.9208) / (ku + kd) -
                  1.96 * math.sqrt((ku * kd) / (ku + kd) + 0.9604) /
                  (ku + kd)) / (1 + 3.8416 / (ku + kd))
        wilson *= 100
    return int(wilson)

@api.errorhandler(400)
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

@api.errorhandler(401)
def error_permission_denied(msg=None):
    """ Error handler: Permission Denied """
    return json_error(msg, 401)

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

@api.route('/api/submit', methods=['POST'])
def submit():
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
        user = db.user_get_by_hash(item['user_hash'])
        if user and user.is_banned:
            return json_error('account has been disabled due to abuse')

        # create new
        review = OdrsReview()
        review.app_id = item['app_id']
        review.locale = item['locale']
        review.summary = item['summary']
        review.description = item['description']
        review.user_hash = item['user_hash']
        review.version = item['version']
        review.distro = item['distro']
        review.rating = item['rating']

        # check if valid
        user_display_ignore = ['root',
                               'Live System User',
                               'Unknown']
        if item['user_display'] not in user_display_ignore:
            review.user_display = item['user_display']

        # log and add
        db.event_info(_get_client_address(),
                      review.user_hash,
                      review.app_id,
                      "reviewed")
        db.review_add(review, _get_client_address())
    except CursorError as e:
        return json_error(str(e))
    return json_success()

@api.route('/api/app/<app_id>/<user_hash>')
@api.route('/api/app/<app_id>')
def app(app_id, user_hash=None):
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
    items_new = []
    for review in reviews:
        if review.reported > 0:
            continue
        item = review.__dict__
        if user_hash:
            item['user_skey'] = _get_user_key(user_hash, review.app_id)
        items_new.append(item)

    dat = json.dumps(items_new, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@api.route('/api/fetch', methods=['POST'])
def fetch():
    """
    Return details about an application.
    """
    try:
        item = json.loads(request.data.decode('utf8'))
    except ValueError as e:
        return json_error(str(e))
    for key in ['app_id', 'user_hash', 'locale', 'distro', 'limit', 'version']:
        if not key in item:
            return json_error('invalid data, expected %s' % key)
        if item[key] is None:
            return json_error('missing data, expected %s' % key)

    # check format
    if not len(item['user_hash']) == 40:
        return json_error('the user_hash is invalid')

    try:
        db = ReviewsDatabase(os.environ)
        db.analytics_inc_fetch(item['app_id'])
        reviews = db.review_get_for_app_id(item['app_id'])
    except CursorError as e:
        return json_error(str(e))

    # if user does not exist then create
    user = db.user_get_by_hash(item['user_hash'])
    if not user:
        db.user_add(item['user_hash'])

    # add score for review using secret sauce
    items_new = []
    for review in reviews:
        if review.reported > 0:
            continue

        # the user isn't going to be able to read this
        if not _locale_is_compatible(review.locale, item['locale']):
            continue

        # return all results
        item_new = review.__dict__
        item_new['user_skey'] = _get_user_key(item['user_hash'], review.app_id)
        item_new['score'] = _get_review_score(review, item)

        # the UI can hide the vote buttons on reviews already voted on
        if db.vote_exists(review.review_id, item['user_hash']):
            item_new['vote_id'] = 1

        items_new.append(item_new)

    # fake something so the user can get the user_skey
    if len(items_new) == 0:
        item_new = {}
        item_new['score'] = 0
        item_new['app_id'] = item['app_id']
        item_new['user_hash'] = item['user_hash']
        item_new['user_skey'] = _get_user_key(item['user_hash'], item['app_id'])
        items_new.append(item_new)

    # sort and cut to limit
    sorted(items_new, key=lambda item: item['score'], reverse=True)
    if item['limit'] > 0:
        items_new = items_new[:item['limit']]

    dat = json.dumps(items_new, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@api.route('/api/all/<user_hash>')
@api.route('/api/all')
def all(user_hash=None):
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
        for review in reviews:
            if review.reported > 0:
                continue
            item = review.__dict__
            item['user_skey'] = _get_user_key(user_hash, review.app_id)

    dat = json.dumps(reviews, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")

@api.route('/api/moderate/<user_hash>')
@api.route('/api/moderate/<user_hash>/<locale>')
def moderate(user_hash, locale=None):
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
    items_new = []
    for review in reviews:
        if locale and not _locale_is_compatible(review.locale, locale):
            continue
        if not db.vote_exists(review.review_id, user_hash):
            item = review.__dict__
            item['user_skey'] = _get_user_key(user_hash, review.app_id)
            items_new.append(item)

    dat = json.dumps(items_new, sort_keys=True, indent=4, separators=(',', ': '))
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
        user = db.user_get_by_hash(item['user_hash'])
        if not user:
            db.user_add(item['user_hash'])
        else:

            # user is naughty
            if user.is_banned:
                return json_error('account has been disabled due to abuse')

            # the user is too harsh
            if val < 0 and user.karma < -50:
                return json_error('all negative karma used up')
        db.user_update_karma(item['user_hash'], val)

        # add the vote to the database
        db.vote_add(item['review_id'], val, item['user_hash'])
        db.event_info(_get_client_address(), item['user_hash'], item['app_id'],
                      "voted %i on review" % val)

    except CursorError as e:
        return json_error(str(e))
    return json_success('voted #%i %i' % (item['review_id'], val))

@api.route('/api/upvote', methods=['POST'])
def upvote():
    """
    Upvote an existing review by one karma point.
    """
    return vote(1)

@api.route('/api/downvote', methods=['POST'])
def downvote():
    """
    Downvote an existing review by one karma point.
    """
    return vote(-1)

@api.route('/api/dismiss', methods=['POST'])
def dismiss():
    """
    Dismiss a review without rating it up or down.
    """
    return vote(0)

@api.route('/api/report', methods=['POST'])
def report():
    """
    Report a review for abuse.
    """
    return vote(-5)

@api.route('/api/remove', methods=['POST'])
def remove():
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

@api.route('/api/ratings/<app_id>')
def rating_for_id(app_id):
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

@api.route('/api/ratings')
def ratings():
    """
    Get the star ratings for a specific application.
    """
    item = {}
    try:
        db = ReviewsDatabase(os.environ)
        app_ids = db.get_all_apps()
        for app_id in app_ids:
            ratings = db.reviews_get_rating_for_app_id(app_id, 2)
            if len(ratings) == 0:
                continue
            item[app_id] = ratings
    except CursorError as e:
        return json_error(str(e))

    dat = json.dumps(item, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype="application/json")
