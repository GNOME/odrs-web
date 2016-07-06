#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

class OdrsReview(object):
    def __init__(self):
        self.review_id = 0
        self.date_created = 0
        self.app_id = None
        self.locale = None
        self.summary = None
        self.description = None
        self.version = None
        self.distro = None
        self.karma = 0
        self.user_hash = None
        self.user_display = None
        self.rating = 0
        self.date_deleted = None
