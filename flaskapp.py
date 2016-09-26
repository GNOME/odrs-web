#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import os
from flask import Flask, request, url_for, redirect, flash, render_template, send_from_directory, abort
from flask.ext.login import LoginManager
from flask.ext.login import login_required, login_user, logout_user

from api10 import api as api10
from admin import admin
from database import ReviewsDatabase, CursorError
from user import OdrsUser

app = Flask(__name__)
app.config.from_object(__name__)
app.register_blueprint(api10, url_prefix='/1.0/reviews')
app.register_blueprint(admin, url_prefix='/admin')

# use the hash as the session key
if 'ODRS_REVIEWS_SECRET' in os.environ:
    app.secret_key = os.environ['ODRS_REVIEWS_SECRET']

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db = ReviewsDatabase(os.environ)
    user = db.user_get_by_id(user_id)
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method != 'POST':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    try:
        db = ReviewsDatabase(os.environ)
        user = db.user_get_with_login(request.form['username'],
                                      request.form['password'])
    except CursorError as e:
        return json_error(str(e))
    if not user:
        flash('Credentials are not valid.')
        return redirect(url_for('.login'))
    login_user(user, remember=False)
    flash('Logged in successfully.')
    return redirect(url_for('.index'))

@app.route("/logout")
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('.index'))

@app.errorhandler(404)
def error_page_not_found(msg=None):
    """ Error handler: File not found """
    flash(msg)
    return render_template('error.html'), 404

@app.route('/')
def index():
    """ start page """
    return render_template('index.html')

@app.route('/oars')
def oars_index():
    """ OARS page """
    return render_template('oars.html')

@app.route('/<path:resource>')
def static_resource(resource):
    """ Return a static image or resource """
    return send_from_directory('static/', resource)

if __name__ == '__main__':
    app.debug = True

    # we need this
    if not 'ODRS_REVIEWS_SECRET' in os.environ:
        os.environ['ODRS_REVIEWS_SECRET'] = 'dummy'
        print('NO ODRS_REVIEWS_SECRET DEFINED, WE ARE INSECURE')

    app.run()
