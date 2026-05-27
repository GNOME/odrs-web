#!/usr/bin/python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0+

import gzip
import os
import subprocess
import sys
import threading
import time
import urllib.request

import brotli


ODRS_HOME = os.environ.get("ODRS_HOME", "/opt/app-root/src")
CRON = os.path.join(ODRS_HOME, "cron.py")
CDN = os.path.join(ODRS_HOME, "cdn-refresh.py")


def run_flask(args):
    subprocess.run(["flask"] + args, cwd=ODRS_HOME, check=True)


def run_script(script, *args):
    subprocess.run([sys.executable, script] + list(args), cwd=ODRS_HOME, check=True)


def run_fsck_loop(interval=43200):
    while True:
        try:
            run_script(CRON, "fsck")
        except Exception as e:
            print(f"fsck error: {e}", file=sys.stderr)
        time.sleep(interval)


def import_appstream():
    dest = "/tmp/appstream.xml.gz"
    urllib.request.urlretrieve(
        "https://dl.flathub.org/repo/appstream/x86_64/appstream.xml.gz", dest
    )
    run_script(CRON, "appstream-import", dest)


def import_badwords():
    dest = "/tmp/badwords.csv"
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/hughsie/badwords/master/badwords.csv", dest
    )
    run_script(CRON, "taboo-import", dest)


def run_ratings_loop(interval=86400):
    ratings_path = "/tmp/ratings/ratings.json"
    while True:
        try:
            run_script(CRON, "ratings", ratings_path)

            with open(ratings_path, "rb") as f:
                raw = f.read()
            with gzip.open(ratings_path + ".gz", "wb") as f:
                f.write(raw)
            with open(ratings_path + ".br", "wb") as f:
                f.write(brotli.compress(raw))

            try:
                run_script(CDN)
            except Exception as e:
                print(f"cdn-refresh error: {e}", file=sys.stderr)

        except Exception as e:
            print(f"ratings loop error: {e}", file=sys.stderr)

        time.sleep(interval)


def start_gunicorn():
    app_module = os.environ.get("APP_MODULE", "odrs:app")
    os.execvp(
        "gunicorn",
        [
            "gunicorn",
            "--bind",
            "0.0.0.0:8080",
            "--workers",
            "4",
            "--access-logfile",
            "-",
            "--error-logfile",
            "-",
            app_module,
        ],
    )


def main():
    os.makedirs("/tmp/ratings", exist_ok=True)

    os.environ.setdefault("FLASK_APP", "odrs:app")
    os.environ.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", "False")

    run_flask(["db", "upgrade"])
    run_flask(["initdb"])

    threading.Thread(target=run_fsck_loop, daemon=True).start()

    import_appstream()
    import_badwords()

    threading.Thread(target=run_ratings_loop, daemon=True).start()

    start_gunicorn()


if __name__ == "__main__":
    main()
