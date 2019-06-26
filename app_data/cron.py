#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import json
import sys

from odrs import db

from odrs.models import Review
from odrs.util import _get_rating_for_app_id

def _regenerate_ratings(fn):
    item = {}

    app_ids = [res[0] for res in db.session.query(Review.app_id).\
                       order_by(Review.app_id.asc()).\
                       distinct(Review.app_id).all()]
    for app_id in app_ids:
        ratings = _get_rating_for_app_id(app_id, 2)
        if len(ratings) == 0:
            continue
        item[app_id] = ratings

    # dump to file
    with open(fn, 'w') as outfd:
        outfd.write(json.dumps(item, sort_keys=True, indent=4, separators=(',', ': ')))

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print('Usage: %s ratings filename' % sys.argv[0])
        sys.exit(1)

    # create the ratings data
    if sys.argv[1] == 'ratings':
        _regenerate_ratings(sys.argv[2])
    else:
        print("cron mode %s not known" % sys.argv[1])
        sys.exit(1)

    # success
    sys.exit(0)
