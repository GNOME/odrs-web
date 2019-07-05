#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# pylint: disable=invalid-name,missing-docstring
#
# Copyright (C) 2015-2019 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import json
import math
import datetime

from collections import defaultdict

from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import IntegrityError

from flask import request, Response

from odrs import app, db

from .models import Review, User, Vote, Analytic, Taboo, Component
from .models import _vote_exists
from .util import json_success, json_error, _locale_is_compatible, _eventlog_add, _get_user_key, _get_datestr_from_dt
from .util import _sanitised_version, _sanitised_summary, _sanitised_description, _get_rating_for_app_id
from .util import _get_taboos_for_locale

ODRS_REPORTED_CNT = 2

def _get_client_address():
    """ Gets user IP address """
    if request.headers.getlist('X-Forwarded-For'):
        return request.headers.getlist('X-Forwarded-For')[0]
    return request.remote_addr

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

def _check_str(val):
    """ Return with success if the summary and description """
    if val.find('<') != -1:
        return False
    if val.find('<') != -1:
        return False
    return True

@app.route('/1.0/reviews/api/submit', methods=['POST'])
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
        if not item[key]:
            return json_error('missing data, expected %s' % key)

    # check format
    if not len(item['user_hash']) == 40:
        return json_error('the user_hash is invalid')

    # check fields for markup and length
    if len(item['summary']) > 70:
        return json_error('summary is too long')
    if len(item['description']) > 3000:
        return json_error('description is too long')
    for key in ['summary', 'description']:
        if not _check_str(item[key]):
            return json_error('%s is not a valid string' % key)

    # check user has not been banned
    user = db.session.query(User).filter(User.user_hash == item['user_hash']).first()
    if user:
        if user.is_banned:
            return json_error('account has been disabled due to abuse')
    else:
        user = User(item['user_hash'])
        db.session.add(user)

    # user has already reviewed
    if db.session.query(Review).\
            join(Component).\
            filter(Component.app_id == item['app_id']).\
            filter(Review.user_id == user.user_id).first():
        _eventlog_add(_get_client_address(),
                      user.user_id,
                      item['app_id'],
                      'already reviewed')
        return json_error('already reviewed this app')

    # component definately exists now!
    component = db.session.query(Component).filter(Component.app_id == item['app_id']).first()
    if component:
        component.review_cnt += 1
    else:
        component = Component(item['app_id'])
        db.session.add(component)
        db.session.commit()

    # create new
    review = Review()
    review.locale = item['locale']
    review.summary = _sanitised_summary(item['summary'])
    review.description = _sanitised_description(item['description'])
    review.user_id = user.user_id
    review.version = _sanitised_version(item['version'])
    review.distro = item['distro']
    review.rating = item['rating']
    review.user_addr = _get_client_address()
    review.component_id = component.component_id

    # check if valid
    user_display_ignore = ['root',
                           'Administrator',
                           'Live System User',
                           'user',
                           'Unknown']
    if item['user_display'] not in user_display_ignore:
        review.user_display = item['user_display']

    # contains taboos
    if review.matches_taboos(_get_taboos_for_locale(review.locale)):
        review.reported = 5

    # log and add
    _eventlog_add(_get_client_address(),
                  review.user_id,
                  component.app_id,
                  'reviewed')
    db.session.add(review)
    db.session.commit()
    return json_success()

@app.route('/1.0/reviews/api/app/<app_id>/<user_hash>')
@app.route('/1.0/reviews/api/app/<app_id>')
def api_show_app(app_id, user_hash=None):
    """
    Return details about an application.
    """
    reviews = db.session.query(Review).\
                    join(Component).\
                    filter(Component.app_id == app_id).\
                    filter(Review.reported < ODRS_REPORTED_CNT).\
                    order_by(Review.date_created.desc()).all()
    items = [review.asdict(user_hash) for review in reviews]
    dat = json.dumps(items, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype='application/json')

@app.route('/1.0/reviews/api/fetch', methods=['POST'])
def api_fetch():
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
        if not item[key]:
            return json_error('missing data, expected %s' % key)

    # check format
    if not len(item['user_hash']) == 40:
        return json_error('the user_hash is invalid')

    # increments the fetch count on one specific application
    datestr = _get_datestr_from_dt(datetime.date.today())
    stmt = insert(Analytic).values(datestr=datestr, app_id=item['app_id'])
    if db.session.bind.dialect.name != 'sqlite': # pylint: disable=no-member
        stmt_ondupe = stmt.on_duplicate_key_update(fetch_cnt=Analytic.fetch_cnt + 1)
    else:
        stmt_ondupe = stmt
    try:
        db.session.execute(stmt_ondupe) # pylint: disable=no-member
        db.session.commit()
    except IntegrityError as e:
        print('ignoring: {}'.format(str(e)))

    # increment the counter for the stats
    component = db.session.query(Component).filter(Component.app_id == item['app_id']).first()
    if component:
        component.fetch_cnt += 1
        db.session.commit()

    # also add any compat IDs
    app_ids = [item['app_id']]
    if 'compat_ids' in item:
        app_ids.extend(item['compat_ids'])
    if component:
        if component.parent:
            if component.parent.app_id not in app_ids:
                app_ids.append(component.parent.app_id)
        for child in component.children:
            if child.app_id not in app_ids:
                app_ids.append(child.app_id)
    reviews = db.session.query(Review).\
                    join(Component).\
                    filter(Component.app_id.in_(app_ids)).\
                    filter(Review.reported < ODRS_REPORTED_CNT).all()

    # if user does not exist then create
    user = db.session.query(User).filter(User.user_hash == item['user_hash']).first()
    if not user:
        user = User(user_hash=item['user_hash'])
        db.session.add(user)
        db.session.commit()

    # add score for review using secret sauce
    items_new = []
    for review in reviews:

        # the user isn't going to be able to read this
        if not _locale_is_compatible(review.locale, item['locale']):
            continue

        # return all results
        item_new = review.asdict(item['user_hash'])
        item_new['score'] = _get_review_score(review, item)
        item_new['user_skey'] = _get_user_key(item['user_hash'], item['app_id'])

        # the UI can hide the vote buttons on reviews already voted on
        if _vote_exists(review.review_id, user.user_id):
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
    items_new.sort(key=lambda item: item['score'], reverse=True)
    if item['limit'] > 0:
        items_new = items_new[:item['limit']]

    dat = json.dumps(items_new, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype='application/json')

@app.route('/1.0/reviews/api/all/<user_hash>')
@app.route('/1.0/reviews/api/all')
def api_all(user_hash=None):
    """
    Return all the reviews on the server as a JSON object.
    """
    reviews = db.session.query(Review).filter(Review.reported < ODRS_REPORTED_CNT).all()
    items = [review.asdict(user_hash) for review in reviews]
    dat = json.dumps(items, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype='application/json')

@app.route('/1.0/reviews/api/moderate/<user_hash>')
@app.route('/1.0/reviews/api/moderate/<user_hash>/<locale>')
def api_moderate(user_hash, locale=None):
    """
    Return all the reviews on the server the user can moderate.
    """
    # only return reviews the user has not already voted on
    items = []
    user = db.session.query(User).filter(User.user_hash == user_hash).first()
    if not user:
        return json_error('no user for {}'.format(user_hash))
    for review in db.session.query(Review).all():
        if locale and not _locale_is_compatible(review.locale, locale):
            continue
        if _vote_exists(review.review_id, user.user_id):
            continue
        items.append(review.asdict(user_hash))
        if len(items) > 250:
            break
    dat = json.dumps(items, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype='application/json')

def _vote(val):
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

    # get user
    user = db.session.query(User).filter(User.user_hash == item['user_hash']).first()
    if not user:
        user = User(item['user_hash'])
        db.session.add(user)
    else:

        # user is naughty
        if user.is_banned:
            return json_error('account has been disabled due to abuse')

        # the user is too harsh
        if val < 0 and user.karma < -50:
            return json_error('all negative karma used up')

    if item['user_skey'] != _get_user_key(item['user_hash'], item['app_id']):
        _eventlog_add(_get_client_address(), user.user_id, None,
                      'invalid user_skey of %s' % item['user_skey'], important=True)
        #print('expected user_skey of %s' % _get_user_key(item['user_hash'], item['app_id']))
        return json_error('invalid user_skey')

    # the user already has a review
    if _vote_exists(item['review_id'], user.user_id):
        _eventlog_add(_get_client_address(), user.user_id, item['app_id'],
                      'duplicate vote')
        return json_error('already voted on this app')

    # update the per-user karma
    user.karma += val

    review = db.session.query(Review).\
                join(Component).\
                filter(Component.app_id == item['app_id']).first()
    if not review:
        _eventlog_add(_get_client_address(), user.user_id, None,
                      'invalid review ID of %s' % item['app_id'], important=True)
        return json_error('invalid review ID')

    # update review
    if val == -5:
        review.reported += 1
    elif val == 1:
        review.karma_up += 1
    elif val == -1:
        review.karma_down += 1

    db.session.commit()

    # add the vote to the database
    db.session.add(Vote(user.user_id, val, review_id=item['review_id']))
    db.session.commit()
    _eventlog_add(_get_client_address(), user.user_id, item['app_id'],
                  'voted %i on review' % val)

    return json_success('voted #%i %i' % (item['review_id'], val))

@app.route('/1.0/reviews/api/upvote', methods=['POST'])
def api_upvote():
    """
    Upvote an existing review by one karma point.
    """
    return _vote(1)

@app.route('/1.0/reviews/api/downvote', methods=['POST'])
def api_downvote():
    """
    Downvote an existing review by one karma point.
    """
    return _vote(-1)

@app.route('/1.0/reviews/api/dismiss', methods=['POST'])
def api_dismiss():
    """
    Dismiss a review without rating it up or down.
    """
    return _vote(0)

@app.route('/1.0/reviews/api/report', methods=['POST'])
def api_report():
    """
    Report a review for abuse.
    """
    return _vote(-5)

@app.route('/1.0/reviews/api/remove', methods=['POST'])
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
        if not item[key]:
            return json_error('missing data, expected %s' % key)

    # check format
    if not len(item['user_hash']) == 40:
        return json_error('the user_hash is invalid')
    if not len(item['user_skey']) == 40:
        return json_error('the user_skey is invalid')

    # the user already has a review
    user = db.session.query(User).filter(User.user_hash == item['user_hash']).first()
    if not user:
        return json_error('no review')
    review = db.session.query(Review).\
                filter(Review.review_id == item['review_id']).\
                filter(Review.user_id == user.user_id).first()
    if not review:
        return json_error('no review')
    if review.component.app_id != item['app_id']:
        return json_error('the app_id is invalid')

    if item['user_skey'] != _get_user_key(item['user_hash'], item['app_id']):
        _eventlog_add(_get_client_address(), user.user_id, None,
                      'invalid user_skey of %s' % item['user_skey'], important=True)
        return json_error('invalid user_skey')

    db.session.delete(review)
    db.session.commit()
    _eventlog_add(_get_client_address(),
                  user.user_id,
                  item['app_id'],
                  'removed review')
    return json_success('removed review #%i' % item['review_id'])

@app.route('/1.0/reviews/api/ratings/<app_id>')
def api_rating_for_id(app_id):
    """
    Get the star ratings for a specific application.
    """
    ratings = _get_rating_for_app_id(app_id)
    dat = json.dumps(ratings, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype='application/json')

@app.route('/1.0/reviews/api/taboo/all')
def api_taboo_all():
    """
    Get the star ratings for a specific application.
    """
    items = defaultdict(list)
    for taboo in db.session.query(Taboo).\
                order_by(Taboo.locale.asc()).\
                order_by(Taboo.value.asc()).all():
        items[taboo.locale].append(taboo.asdict())
    dat = json.dumps(items, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype='application/json')

@app.route('/1.0/reviews/api/ratings')
def api_ratings():
    """
    Get the star ratings for all known applications.
    """
    item = {}
    app_ids = [res[0] for res in db.session.query(Component.app_id).\
                                       order_by(Component.app_id.asc()).\
                                       distinct(Component.app_id).all()]
    for app_id in app_ids:
        ratings = _get_rating_for_app_id(app_id, 2)
        if len(ratings) == 0:
            continue
        item[app_id] = ratings

    dat = json.dumps(item, sort_keys=True, indent=4, separators=(',', ': '))
    return Response(response=dat,
                    status=200, \
                    mimetype='application/json')
