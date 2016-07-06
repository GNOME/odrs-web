#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

class OdrsEvent(object):
    def __init__(self):
        self.eventlog_id = 0
        self.date_created = 0
        self.user_addr = None
        self.user_hash = None
        self.message = None
        self.app_id = None
        self.important = False
