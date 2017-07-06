#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# pylint: disable=invalid-name,missing-docstring
#
# Copyright (C) 2015-2017 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 2

import os

from flask import Flask, flash, render_template
from flask_login import LoginManager

from .db import Database

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = os.environ['ODRS_REVIEWS_SECRET']

lm = LoginManager()
lm.init_app(app)

db = Database(app)

@lm.user_loader
def load_user(user_id):
    user = db.user_get_by_id(user_id)
    return user

@app.errorhandler(404)
def error_page_not_found(msg=None):
    """ Error handler: File not found """
    flash(msg)
    return render_template('error.html'), 404

from app import views
from app import views_admin
