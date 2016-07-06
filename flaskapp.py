#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import os
from flask import Flask, request, url_for, redirect, flash, render_template, send_from_directory
from flask.ext.login import LoginManager
from flask.ext.login import login_required, login_user, logout_user
from reviews import reviews

app = Flask(__name__)
app.config.from_pyfile('flaskapp.cfg')
app.register_blueprint(reviews, url_prefix='/1.0/reviews')

login_manager = LoginManager()
login_manager.init_app(app)

class User(object):
    def __init__(self):
        self.id = None
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


@login_manager.user_loader
def load_user(user_id):
    #return User.get(user_id)
    print("USERID:%s" % user_id)
    user = User()
    user_id = 998
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method != 'POST':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    print(username,password)
    user = User()
    user.id = 99
    login_user(user, remember=False)
    ##fixme
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
    if not 'OPENSHIFT_APP_DNS' in os.environ:
        app.debug = True

    # we need this
    if not 'ODRS_REVIEWS_SECRET' in os.environ:
        print('NO ODRS_REVIEWS_SECRET DEFINED, WE ARE INSECURE')

    app.run()
