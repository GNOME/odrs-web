#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import sys
import os
sys.path.insert(0, os.path.join(os.environ['HOME'], 'html'))
from flaskapp import app as application
