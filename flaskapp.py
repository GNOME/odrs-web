#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import os
from flask import Flask, flash, render_template, send_from_directory
from reviews import reviews

app = Flask(__name__)
app.config.from_pyfile('flaskapp.cfg')
app.register_blueprint(reviews, url_prefix='/1.0/reviews')

@app.errorhandler(404)
def error_page_not_found(msg=None):
    """ Error handler: File not found """
    flash(msg)
    return render_template('error.html'), 404

@app.route('/')
def fwupd_index():
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
