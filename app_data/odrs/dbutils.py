#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

def init_db(db):

    # ensure all tables exist
    db.metadata.create_all(bind=db.engine)

    # ensure admin user exists
    from .models import Moderator
    if not db.session.query(Moderator).filter(Moderator.username == 'admin@test.com').first():
        mod = Moderator(username='admin@test.com')
        mod.password = 'Pa$$w0rd'
        mod.is_admin = True
        db.session.add(mod)
        db.session.commit()

def drop_db(db):
    db.metadata.drop_all(bind=db.engine)
