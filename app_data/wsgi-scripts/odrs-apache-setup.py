#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import sys
import os

def subst_inplace(fn):
    with open(fn, 'r') as f:
        blob = f.read()
    for key in ['SQLALCHEMY_DATABASE_URI',
                'ODRS_REVIEWS_SECRET']:
        search = '%%{ENV:%s}' % format(key)
        blob = blob.replace(search, os.environ.get(key, 'INVALID'))
    with open(fn, 'w') as f:
        f.write(blob)

if __name__ == '__main__':
    for argv in sys.argv[1:]:
        print('Processing', argv)
        subst_inplace(argv)
