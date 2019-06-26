#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# pylint: disable=invalid-name,missing-docstring,wrong-import-order,wrong-import-position
#
# Copyright (C) 2015-2017 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import os

from flask import Flask, flash, render_template, g
from flask_login import LoginManager

from .db import Database

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = os.environ['ODRS_REVIEWS_SECRET']

lm = LoginManager()
lm.init_app(app)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g.db = Database(app)
    return db

@app.teardown_appcontext
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@lm.user_loader
def load_user(user_id):
    db = get_db()
    user = db.moderators.get_by_id(user_id)
    return user

@app.errorhandler(404)
def error_page_not_found(msg=None):
    """ Error handler: File not found """
    flash(msg)
    return render_template('error.html'), 404

from odrs import views
from odrs import views_admin
