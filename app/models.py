#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# pylint: disable=invalid-name,missing-docstring,too-few-public-methods
#
# Copyright (C) 2015-2017 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 2

class User(object):
    def __init__(self):
        self.id = None
        self.karma = 0
        self.date_created = 0
        self.user_hash = 0
        self.is_banned = 0

class Review(object):
    def __init__(self):
        self.review_id = 0
        self.date_created = 0
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
        self.date_deleted = None
        self.reported = None

class Event(object):
    def __init__(self):
        self.eventlog_id = 0
        self.date_created = 0
        self.user_addr = None
        self.user_hash = None
        self.message = None
        self.app_id = None
        self.important = False

class Moderator(object):
    def __init__(self):
        self.moderator_id = 0
        self.username = None
        self.password = None
        self.display_name = None
        self.email = None
        self.is_enabled = False
        self.is_admin = False
        self.user_hash = None
        self.locales = None

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
        return '<Moderator %r>' % (self.moderator_id)
