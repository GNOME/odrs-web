#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# pylint: disable=invalid-name,missing-docstring,too-few-public-methods,too-many-instance-attributes
#
# Copyright (C) 2015-2019 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import Column, Integer, String, Text, DateTime, Index

from odrs import db

from .util import _password_hash, _get_user_key

def _vote_exists(review_id, user_hash):
    """ Checks to see if a vote exists for the review+user """
    return db.session.query(Vote).\
                filter(Vote.review_id == review_id).\
                filter(Vote.user_hash == user_hash).\
                first()

class Analytic(db.Model):

    # sqlalchemy metadata
    __tablename__ = 'analytics'
    __table_args__ = (Index('datestr', 'datestr', 'app_id', unique=True),
                      {'mysql_character_set': 'utf8mb4'}
                     )

    datestr = Column(Integer, default=0, primary_key=True)
    app_id = Column(String(128), primary_key=True)
    fetch_cnt = Column(Integer, default=1)

    def __init__(self):
        self.datestr = None

    def __repr__(self):
        return 'Analytic object %s' % self.analytic_id

class Vote(db.Model):

    # sqlalchemy metadata
    __tablename__ = 'votes'
    __table_args__ = {'mysql_character_set': 'utf8mb4'}

    vote_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    user_hash = Column(Text)
    val = Column(Integer, default=0)
    review_id = Column(Integer, default=0)

    def __init__(self, user_hash, val, review_id=0):
        self.review_id = review_id
        self.user_hash = user_hash
        self.val = val

    def __repr__(self):
        return 'Vote object %s' % self.vote_id

class User(db.Model):

    # sqlalchemy metadata
    __tablename__ = 'users'
    __table_args__ = {'mysql_character_set': 'utf8mb4'}
    __table_args__ = (Index('users_hash_idx', 'user_hash'),
                      {'mysql_character_set': 'utf8mb4'}
                     )

    user_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    user_hash = Column(Text)
    karma = Column(Integer, default=0)
    is_banned = Column(Integer, default=0)

    def __init__(self, user_hash=None):
        self.user_hash = user_hash
        self.karma = 0
        self.is_banned = 0

    def __repr__(self):
        return 'User object %s' % self.user_id

class Review(db.Model):

    # sqlalchemy metadata
    __tablename__ = 'reviews'
    __table_args__ = {'mysql_character_set': 'utf8mb4'}

    review_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    date_deleted = Column(DateTime)
    app_id = Column(Text)
    locale = Column(Text)
    summary = Column(Text)
    description = Column(Text)
    user_hash = Column(Text)
    user_addr = Column(Text)
    user_display = Column(Text)
    version = Column(Text)
    distro = Column(Text)
    rating = Column(Integer, default=0)
    karma_up = Column(Integer, default=0)
    karma_down = Column(Integer, default=0)
    reported = Column(Integer, default=0)

    def __init__(self):
        self.app_id = None
        self.locale = None
        self.summary = None
        self.description = None
        self.version = None
        self.distro = None
        self.karma_up = 0
        self.karma_down = 0
        self.user_hash = None
        self.user_display = None
        self.rating = 0
        self.reported = 0

    def asdict(self, user_hash=None):
        item = {
            'app_id': self.app_id,
            'date_created': self.date_created.timestamp(),
            'description': self.description,
            'distro': self.distro,
            'karma_down': self.karma_down,
            'karma_up': self.karma_up,
            'locale': self.locale,
            'rating': self.rating,
            'reported': self.reported,
            'review_id': self.review_id,
            'summary': self.summary,
            'user_display': self.user_display,
            'user_hash': self.user_hash,
            'version': self.version,
        }
        if user_hash:
            item['user_skey'] = _get_user_key(user_hash, self.app_id)
        return item

    def __repr__(self):
        return 'Review object %s' % self.review_id

class Event(db.Model):

    # sqlalchemy metadata
    __tablename__ = 'eventlog'
    __table_args__ = (Index('message_idx', 'message', mysql_length=8),
                      Index('date_created_idx', 'date_created'),
                      {'mysql_character_set': 'utf8mb4'}
                     )

    eventlog_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    user_addr = Column(Text)
    user_hash = Column(Text)
    message = Column(Text)
    app_id = Column(Text)
    important = Column(Integer, default=0)

    def __init__(self, user_addr, user_hash=None, app_id=None, message=None, important=False):
        self.user_addr = user_addr
        self.user_hash = user_hash
        self.message = message
        self.app_id = app_id
        self.important = important

    def __repr__(self):
        return 'Event object %s' % self.eventlog_id

class Moderator(db.Model):

    # sqlalchemy metadata
    __tablename__ = 'moderators'
    __table_args__ = {'mysql_character_set': 'utf8mb4'}

    moderator_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    username = Column(Text)
    password_hash = Column('password', Text)
    display_name = Column(Text)
    email = Column(Text)
    is_enabled = Column(Integer, default=0)
    is_admin = Column(Integer, default=0)
    user_hash = Column(Text)
    locales = Column(Text)

    def __init__(self, username=None, password=None, display_name=None, email=None):
        self.username = username
        self.display_name = display_name
        self.email = email
        self.is_enabled = False
        self.is_admin = False
        self.user_hash = None
        self.locales = None
        self.locales = password

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        # on success, upgrade the old hashing function to the new secure one
        if len(self.password_hash) == 40:
            if self.password_hash != _password_hash(password):
                return False
            self.password = password
            return True
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.moderator_id)

    def __repr__(self):
        return 'Moderator object %s' % self.moderator_id
