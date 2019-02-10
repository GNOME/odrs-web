#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2018 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

from __future__ import print_function

import json
import sys

from app.db import Database, CursorError

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print('Usage: %s ratings filename' % sys.argv[0])
        sys.exit(1)

    # create the ratings data
    if sys.argv[1] == 'ratings':
        item = {}
        try:
            db = Database(None)
            app_ids = db.reviews.get_all_apps()
            for app_id in app_ids:
                ratings = db.reviews.get_rating_for_app_id(app_id, 2)
                if len(ratings) == 0:
                    continue
                item[app_id] = ratings
        except CursorError as e:
            print(str(e))
            sys.exit(1)

        # dump to file
        dat = json.dumps(item, sort_keys=True, indent=4, separators=(',', ': '))
        outfd = open(sys.argv[2], "w")
        outfd.write(dat)
        outfd.close()
    else:
        print("cron mode %s not known" % sys.argv[1])
        sys.exit(1)

    # success
    sys.exit(0)
