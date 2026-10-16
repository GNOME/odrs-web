#!/usr/bin/python3
#
# Copyright (C) 2018 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+

import os
import sys

from glob import glob
from pylint.lint import Run


def main():

    # find python files
    filenames = [y for x in os.walk(".") for y in glob(os.path.join(x[0], "*.py"))]
    argv = ["-j", "8", "--rcfile", "contrib/pylintrc"]
    files = []
    for fn in sorted(filenames):
        if fn.find("migrations/") != -1:
            continue
        if fn.startswith("./env"):
            continue
        print("Checking %s" % fn)
        files.append(fn)

    return Run(argv + files, exit=False).linter.msg_status


if __name__ == "__main__":
    sys.exit(main())
