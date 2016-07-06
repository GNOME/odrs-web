#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

class OdrsUser(object):
    def __init__(self):
        self.id = None
        self.karma = 0
        self.date_created = 0
        self.user_hash = 0
        self.is_banned = 0

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
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % (self.nickname)
