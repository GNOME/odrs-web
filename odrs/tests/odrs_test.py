#!/usr/bin/python3
#
# Copyright (C) 2019 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-3.0+
#
# pylint: disable=fixme,too-many-public-methods,line-too-long,too-many-lines
# pylint: disable=too-many-instance-attributes,wrong-import-position,import-outside-toplevel

import os
import json
import sys
import unittest
import datetime

# allows us to run this from the project root
sys.path.append(os.path.realpath("."))

from odrs.util import _get_user_key


class OdrsTest(unittest.TestCase):
    def setUp(self):

        self.user_hash = "deadbeef348c0f88529f3bfd937ec1a5d90aefc7"

        # create instance
        import odrs
        from odrs import db
        from odrs.dbutils import init_db, drop_db

        odrs.app.config["SECRET_KEY"] = "not-secret4"
        odrs.app.config["ODRS_REVIEWS_SECRET"] = "1"
        odrs.app.config["WTF_CSRF_CHECK_DEFAULT"] = False
        odrs.app.config["DEBUG"] = True

        self.app = odrs.app.test_client()
        with odrs.app.app_context():
            drop_db(db)
            init_db(db)

        # assign user_hash to this account
        self.login()
        rv = self.app.post(
            "/admin/moderator/1/modify_by_admin",
            data=dict(
                is_enabled=True,
                is_admin=True,
                locales="en",
                user_hash=self.user_hash,
            ),
            follow_redirects=True,
        )
        assert b"Updated profile" in rv.data, rv.data
        self.logout()

    def tearDown(self):
        pass

    def _login(self, username, password="Pa$$w0rd"):
        return self.app.post(
            "/login",
            data=dict(username=username, password=password),
            follow_redirects=True,
        )

    def _logout(self):
        return self.app.get("/logout", follow_redirects=True)

    def login(self, username="admin@test.com", password="Pa$$w0rd"):
        rv = self._login(username, password)
        assert b"Logged in" in rv.data, rv.data
        assert b"/admin/show/reported" in rv.data, rv.data
        assert b"Incorrect username" not in rv.data, rv.data

    def logout(self):
        rv = self._logout()
        assert b"Logged out" in rv.data, rv.data
        assert b"/admin/show/reported" not in rv.data, rv.data

    def test_admin_show_review_for_app(self):

        self.review_submit()
        self.login()
        rv = self.app.get("/admin/show/app/inkscape.desktop")
        assert b"n essential part of my daily" in rv.data, rv.data

    def test_admin_graphs(self):

        self.review_submit()
        self.review_fetch()
        self.review_fetch()
        self.review_fetch()

        self.login()
        rv = self.app.get("/admin/graph_month")
        assert b"Chart.js" in rv.data, rv.data
        assert b"0, 1" in rv.data, rv.data

        rv = self.app.get("/admin/graph_year")
        assert b"Chart.js" in rv.data, rv.data
        assert b"0, 1" in rv.data, rv.data

        rv = self.app.get("/admin/stats")
        assert b"Chart.js" in rv.data, rv.data
        assert b"Active reviews</td>\n    <td>1</td>" in rv.data, rv.data
        assert b"Haters Gonna Hate" in rv.data, rv.data

    def test_admin_unreport(self):

        self.review_submit()
        self.review_report()

        self.login()
        rv = self.app.get("/admin/unreport/1", follow_redirects=True)
        assert b"Review unreported" in rv.data, rv.data

    def test_admin_review(self):

        rv = self._review_submit(locale="in_IN")
        assert b'"success": true' in rv.data, rv.data

        self.login()
        rv = self.app.get("/admin/review/1")
        assert (
            b"Inkscape has been a essential part of my workflow for many years"
            in rv.data
        ), rv.data
        assert b"Somebody Important" in rv.data, rv.data
        assert b"Fedora" in rv.data, rv.data
        rv = self.app.post(
            "/admin/modify/1",
            data=dict(
                distro="Ubuntu",
            ),
            follow_redirects=True,
        )
        assert (
            b"Inkscape has been a essential part of my workflow for many years"
            in rv.data
        ), rv.data
        assert b"Ubuntu" in rv.data, rv.data

        rv = self.app.get("/admin/englishify/1", follow_redirects=True)
        assert b"en_IN" in rv.data, rv.data

        rv = self.app.get("/admin/anonify/1", follow_redirects=True)
        assert b"Somebody Important" not in rv.data, rv.data

        rv = self.app.get("/admin/vote/1/down", follow_redirects=True)
        assert b"Recorded vote" in rv.data, rv.data

        # delete
        rv = self.app.get("/admin/delete/1", follow_redirects=True)
        assert b"Confirm Removal?" in rv.data, rv.data
        rv = self.app.get("/admin/delete/1/force", follow_redirects=True)
        assert b"Deleted review" in rv.data, rv.data
        rv = self.app.get("/admin/review/1", follow_redirects=True)
        assert b"No review with that ID" in rv.data, rv.data

    def _admin_moderator_add(self, username="dave@dave.com", password="foobarbaz123."):

        return self.app.post(
            "/admin/moderator/add",
            data=dict(
                password_new=password,
                username_new=username,
                display_name="Dave",
            ),
            follow_redirects=True,
        )

    def test_admin_add_moderator(self):

        self.login()

        # bad values
        rv = self._admin_moderator_add(username="1")
        assert b"Username invalid" in rv.data, rv.data
        rv = self._admin_moderator_add(password="foo")
        assert b"The password is too short" in rv.data, rv.data
        rv = self._admin_moderator_add(password="foobarbaz")
        assert b"requires at least one non-alphanumeric" in rv.data, rv.data
        rv = self._admin_moderator_add(username="foo")
        assert b"Invalid email address" in rv.data, rv.data

        # good values
        rv = self._admin_moderator_add()
        assert b"Added user" in rv.data, rv.data

        # duplicate
        rv = self._admin_moderator_add()
        assert b"Already a entry with that username" in rv.data, rv.data
        self.logout()

        # test this actually works
        self.login(username="dave@dave.com", password="foobarbaz123.")
        self.logout()

        # remove
        self.login()
        rv = self.app.get("admin/moderator/2/delete", follow_redirects=True)
        assert b"Deleted user" in rv.data, rv.data

    def test_admin_show_reviews(self):

        self.review_submit()
        self.login()
        rv = self.app.get("/admin/show/all")
        assert b"An essential " in rv.data, rv.data

        rv = self.app.get("/admin/show/lang/en_US")
        assert b"An essential " in rv.data, rv.data
        rv = self.app.get("/admin/show/lang/fr_FR")
        assert b"An essential " not in rv.data, rv.data

    def test_admin_moderators(self):

        self.login()
        rv = self.app.get("/admin/moderators/all")
        assert self.user_hash.encode() in rv.data, rv.data

    def test_admin_search(self):

        self.review_submit()
        self.login()
        rv = self.app.get("/admin/search?value=notgoingtoexist")
        assert b"There are no results for this query" in rv.data, rv.data
        rv = self.app.get("/admin/search?value=inkscape+notgoingtoexist")
        assert b"Somebody Import" in rv.data, rv.data

    def _admin_taboo_add(
        self, locale="en", value="inkscape", description="ola!", severity=0
    ):
        data = {
            "locale": locale,
            "value": value,
            "description": description,
            "severity": severity,
        }
        return self.app.post("/admin/taboo/add", data=data, follow_redirects=True)

    def test_admin_components(self):

        self.review_submit()
        self.review_submit(app_id="inkscape-ubuntu-lts.desktop")
        self.login()
        rv = self.app.get("/admin/component/all")
        assert b"inkscape.desktop" in rv.data, rv.data
        assert b"inkscape-ubuntu-lts.desktop" in rv.data, rv.data

        rv = self.app.get(
            "/admin/component/join/notgoingtoexist.desktop/inkscape-ubuntu-lts.desktop",
            follow_redirects=True,
        )
        assert b"No parent component found" in rv.data, rv.data
        rv = self.app.get(
            "/admin/component/join/inkscape.desktop/notgoingtoexist.desktop",
            follow_redirects=True,
        )
        assert b"No child component found" in rv.data, rv.data
        rv = self.app.get(
            "/admin/component/join/inkscape.desktop/inkscape.desktop",
            follow_redirects=True,
        )
        assert b"Parent and child components were the same" in rv.data, rv.data
        rv = self.app.get(
            "/admin/component/join/inkscape.desktop/inkscape-ubuntu-lts.desktop",
            follow_redirects=True,
        )
        assert b"Joined components" in rv.data, rv.data

        # again
        rv = self.app.get(
            "/admin/component/join/inkscape.desktop/inkscape-ubuntu-lts.desktop",
            follow_redirects=True,
        )
        assert b"Parent and child already set up" in rv.data, rv.data

        # delete inkscape.desktop
        rv = self._api_review_delete()
        assert b"removed review #1" in rv.data, rv.data

        # still match for the alternate name
        self.review_fetch()

    def test_admin_component_delete(self):
        self.review_submit()
        self.review_submit(app_id="inkscape-ubuntu-lts.desktop")
        self.login()

        # delete one, causing the review to get deleted too
        rv = self.app.get("/admin/component/delete/99999", follow_redirects=True)
        assert b"Unable to find component" in rv.data, rv.data
        rv = self.app.get("/admin/component/delete/2", follow_redirects=True)
        assert b"Deleted component with 1 reviews" in rv.data, rv.data

        # still match for the alternate name
        self.review_fetch()

        rv = self.app.get("/admin/component/delete/1", follow_redirects=True)
        assert b"Deleted component with 1 reviews" in rv.data, rv.data

    def test_admin_taboo(self):

        self.login()

        rv = self.app.get("/admin/taboo/all")
        assert b"There are no taboos stored" in rv.data, rv.data

        # add taboos
        rv = self._admin_taboo_add()
        assert b"Added taboo" in rv.data, rv.data
        assert b"inkscape" in rv.data, rv.data
        rv = self._admin_taboo_add()
        assert b"Already added that taboo" in rv.data, rv.data
        rv = self._admin_taboo_add(locale="fr_FR")
        assert b"Added taboo" in rv.data, rv.data

        # submit something, and ensure it's flagged
        rv = self._review_submit()
        assert b"review contains taboo word" in rv.data, rv.data

        # delete
        rv = self.app.get("/admin/taboo/1/delete", follow_redirects=True)
        assert b"Deleted taboo" in rv.data, rv.data
        rv = self.app.get("/admin/taboo/1/delete", follow_redirects=True)
        assert b"No taboo with ID" in rv.data, rv.data

    def test_api_submit_when_banned(self):

        # submit abusive review
        self.review_submit()

        # add user to the ban list
        self.login()
        rv = self.app.get(
            f"/admin/user_ban/{self.user_hash}", follow_redirects=True
        )
        assert b"Banned user" in rv.data, rv.data
        assert b"deleted 1 reviews" in rv.data, rv.data
        self.logout()

        # try to submit another review
        rv = self._review_submit(app_id="gimp.desktop")
        assert b"account has been disabled due to abuse" in rv.data, rv.data

    def test_login_logout(self):

        # test logging in and out
        rv = self._login("admin@test.com", "Pa$$w0rd")
        assert b"/admin/show/reported" in rv.data, rv.data
        rv = self._logout()
        rv = self._login("admin@test.com", "Pa$$w0rd")
        assert b"/admin/show/reported" in rv.data, rv.data
        rv = self._logout()
        assert b"/admin/show/reported" not in rv.data, rv.data
        rv = self._login("FAILED@test.com", "default")
        assert b"Incorrect username" in rv.data, rv.data
        rv = self._login("admin@test.com", "defaultx")
        assert b"Incorrect password" in rv.data, rv.data

    @staticmethod
    def run_cron_regenerate_ratings(fn="test.json"):

        from odrs import app
        from cron import _regenerate_ratings

        with app.test_request_context():
            _regenerate_ratings(fn)

    @staticmethod
    def run_cron_auto_delete():

        from odrs import app
        from cron import _auto_delete

        with app.test_request_context():
            _auto_delete(0)

    def test_nologin_required(self):

        # all these are viewable without being logged in
        uris = [
            "/",
            "/privacy",
        ]
        for uri in uris:
            rv = self.app.get(uri, follow_redirects=True)
            assert b"favicon.ico" in rv.data, rv.data
            assert b"Error!" not in rv.data, rv.data

    def _review_submit(
        self,
        app_id=None,
        locale="en_US",
        distro="Fedora",
        version="2:1.2.3~dsg",
        summary=" An essential part of my daily workflow",
        user_hash=None,
        user_skey=None,
        user_display="Somebody Important",
    ):
        if not app_id:
            app_id = "inkscape.desktop"
        if not user_hash:
            user_hash = self.user_hash
        if not user_skey:
            user_skey = _get_user_key(user_hash, app_id)
        # upload a review
        data = {
            "app_id": app_id,
            "locale": locale,
            "summary": summary,
            "description": "Inkscape has been a essential part of my workflow for many years now.",
            "user_hash": user_hash,
            "user_skey": user_skey,
            "user_display": user_display,
            "distro": distro,
            "rating": 100,
            "version": version,
        }
        return self.app.post(
            "/1.0/reviews/api/submit", data=json.dumps(data), follow_redirects=True
        )

    def review_submit(self, app_id=None, user_hash=None):
        rv = self._review_submit(app_id=app_id, user_hash=user_hash)
        assert b'"success": true' in rv.data, rv.data

    def _review_fetch(
        self,
        app_id="inkscape.desktop",
        user_hash=None,
        locale="en_US",
        distro="Fedora",
        compat_ids=None,
        version="1.2.3",
        anonymous=False,
        limit=5,
        start=0,
    ):
        if not user_hash:
            user_hash = self.user_hash
        # fetch some reviews
        data = {
            "app_id": app_id,
            "locale": locale,
            "distro": distro,
            "limit": limit,
            "start": start,
            "version": version,
        }
        if not anonymous:
            data["user_hash"] = user_hash
        if compat_ids:
            data["compat_ids"] = compat_ids
        return self.app.post(
            "/1.0/reviews/api/fetch", data=json.dumps(data), follow_redirects=True
        )

    def review_fetch(self):
        rv = self._review_fetch(app_id="inkscape.desktop")
        assert b"An essential part of my daily workflow" in rv.data, rv.data

    def test_api_moderate_locale(self):

        rv = self.app.get(f"/1.0/reviews/api/moderate/{self.user_hash}/en_GB")
        assert rv.data == b"[]", rv.data
        self.review_submit()
        rv = self.app.get(f"/1.0/reviews/api/moderate/{self.user_hash}/en_GB")
        assert b"Somebody Important" in rv.data, rv.data
        rv = self.app.get(f"/1.0/reviews/api/moderate/{self.user_hash}/fr_FR")
        assert rv.data == b"[]", rv.data

    def test_api_fetch_anonymous(self):
        from odrs import app, db
        from odrs.models import Event, User, Vote

        self.review_submit()
        self.assertEqual(self.review_upvote().status_code, 200)
        with app.app_context():
            counts = [db.session.query(model).count() for model in (User, Vote, Event)]

        rv = self._review_fetch(anonymous=True)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.mimetype, "application/json")
        items = rv.get_json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["summary"], "An essential part of my daily workflow")
        # Author identity remains public; reader-specific fields are omitted.
        self.assertEqual(items[0]["user_hash"], self.user_hash)
        self.assertNotIn("user_skey", items[0])
        self.assertNotIn("vote_id", items[0])
        self.assertNotIn("user_addr", items[0])

        for options in (
            {"app_id": "not-going-to-exist.desktop"},
            {"locale": "fr_FR"},
            {"start": 5},
        ):
            with self.subTest(options=options):
                rv = self._review_fetch(anonymous=True, **options)
                self.assertEqual(rv.status_code, 200)
                self.assertEqual(rv.get_json(), [])

        with app.app_context():
            self.assertEqual(
                [db.session.query(model).count() for model in (User, Vote, Event)],
                counts,
            )

        # Anonymous requests must not affect a later personalized response.
        rv = self._review_fetch()
        self.assertTrue(rv.cache_control.private)
        item = rv.get_json()[0]
        self.assertEqual(item["vote_id"], 1)
        self.assertEqual(
            item["user_skey"], _get_user_key(self.user_hash, "inkscape.desktop")
        )

    def test_api_fetch_anonymous_filters_and_pagination(self):
        from odrs import app, db
        from odrs.models import Review
        from odrs.util import ODRS_CUTOFF_YEARS, ODRS_REPORTED_CNT

        # Only the two English, recent, unreported reviews should be returned.
        for index, locale in enumerate(("en_US", "en_GB", "fr_FR", "en_US", "en_US")):
            rv = self._review_submit(user_hash=str(index) * 40, locale=locale)
            self.assertEqual(rv.status_code, 200)
        with app.app_context():
            reviews = db.session.query(Review).order_by(Review.review_id).all()
            reviews[0].karma_up = 100
            reviews[3].reported = ODRS_REPORTED_CNT
            reviews[4].date_created = datetime.datetime.now() - datetime.timedelta(
                days=ODRS_CUTOFF_YEARS * 365 + 1
            )
            db.session.commit()

        items = self._review_fetch(anonymous=True, limit=0).get_json()
        self.assertEqual([item["review_id"] for item in items], [1, 2])
        self.assertGreater(items[0]["score"], items[1]["score"])
        personalized = self._review_fetch(limit=0).get_json()
        for item in personalized:
            item.pop("user_skey")
        self.assertEqual(items, personalized)
        self.assertEqual(
            self._review_fetch(anonymous=True, start=1, limit=1).get_json(),
            items[1:2],
        )

    def test_api_fetch_anonymous_compat_id(self):
        from odrs import app, db
        from odrs.models import Component

        self.review_submit()
        expected = self._review_fetch(anonymous=True).get_json()
        rv = self._review_fetch(
            anonymous=True, app_id="alias.desktop", compat_ids=["inkscape.desktop"]
        )
        self.assertEqual(rv.get_json(), expected)

        # Server-side component aliases work without a reader identity too.
        with app.app_context():
            parent = db.session.query(Component).filter_by(app_id="inkscape.desktop").one()
            child = Component("alias.desktop")
            child.parent = parent
            db.session.add(child)
            db.session.commit()
        rv = self._review_fetch(anonymous=True, app_id="alias.desktop")
        self.assertEqual(rv.get_json(), expected)

    def test_api_fetch_invalid_user_hash(self):
        from odrs import app, db
        from odrs.models import User

        data = {
            "app_id": "inkscape.desktop",
            "locale": "en_US",
            "distro": "Fedora",
            "limit": 5,
            "version": "1.2.3",
        }
        with app.app_context():
            count = db.session.query(User).count()
        for value in (
            None, "", False, True, 0, 1, 1.5, [], {}, "a" * 39, "a" * 41,
            ["a"] * 40, {str(i): "a" for i in range(40)},
        ):
            with self.subTest(user_hash=value):
                rv = self.app.post(
                    "/1.0/reviews/api/fetch", json=dict(data, user_hash=value)
                )
                self.assertEqual(rv.status_code, 400)
                self.assertFalse(rv.get_json()["success"])
                self.assertEqual(rv.get_json()["msg"], "the user_hash is invalid")
        with app.app_context():
            self.assertEqual(db.session.query(User).count(), count)

    def test_api_fetch_invalid_body(self):
        for value in (None, False, 1, "app_id", [], ["app_id"], {}):
            with self.subTest(body=value):
                rv = self.app.post("/1.0/reviews/api/fetch", data=json.dumps(value))
                self.assertEqual(rv.status_code, 400)
                self.assertFalse(rv.get_json()["success"])

    def test_api_write_requires_user_hash(self):
        self.review_submit()
        self.assertEqual(self._review_fetch(anonymous=True).status_code, 200)
        data = {
            "review_id": 1,
            "app_id": "inkscape.desktop",
            "locale": "en_US",
            "distro": "Fedora",
            "version": "1.2.3",
            "summary": "A useful app",
            "description": "I use this app every day.",
            "rating": 100,
            "user_display": "A Reader",
            "user_skey": _get_user_key(self.user_hash, "inkscape.desktop"),
        }
        for endpoint in ("submit", "upvote", "downvote", "report", "dismiss", "remove"):
            with self.subTest(endpoint=endpoint):
                rv = self.app.post("/1.0/reviews/api/" + endpoint, json=data)
                self.assertEqual(rv.status_code, 400)
                self.assertFalse(rv.get_json()["success"])
                self.assertIn("user_hash", rv.get_json()["msg"])
        item = self._review_fetch().get_json()[0]
        self.assertEqual(item["karma_up"], 0)
        self.assertEqual(item["karma_down"], 0)
        self.assertEqual(item["reported"], 0)
        self.assertNotIn("vote_id", item)

    def test_api_fetch_new_user(self):
        from odrs import app, db
        from odrs.models import User

        user_hash = "1" * 40
        with app.app_context():
            self.assertIsNone(db.session.query(User).filter_by(user_hash=user_hash).first())
        rv = self._review_fetch(user_hash=user_hash)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(
            rv.get_json(),
            [{
                "app_id": "inkscape.desktop",
                "score": 0,
                "user_hash": user_hash,
                "user_skey": _get_user_key(user_hash, "inkscape.desktop"),
            }],
        )
        with app.app_context():
            self.assertEqual(db.session.query(User).filter_by(user_hash=user_hash).count(), 1)
        self.review_submit()
        rv = self._review_fetch(user_hash=user_hash)
        self.assertNotIn("vote_id", rv.get_json()[0])
        self.assertEqual(
            rv.get_json()[0]["user_skey"], _get_user_key(user_hash, "inkscape.desktop")
        )
        self.assertEqual(self.review_upvote(user_hash=user_hash).status_code, 200)
        self.assertEqual(self._review_fetch(user_hash=user_hash).get_json()[0]["vote_id"], 1)

    def test_api_fetch_anonymous_then_write(self):
        self.review_submit()
        review = self._review_fetch(anonymous=True).get_json()[0]
        self.assertNotIn("user_skey", review)
        data = {
            "app_id": review["app_id"],
            "review_id": review["review_id"],
            "user_hash": self.user_hash,
        }
        # Reading anonymously is not sufficient to obtain a write key.
        other_user_key = self._review_fetch(user_hash="1" * 40).get_json()[0]["user_skey"]
        other_app_key = self._review_fetch(app_id="gimp.desktop").get_json()[0]["user_skey"]
        for endpoint in ("upvote", "downvote", "report", "dismiss", "remove"):
            for key in (None, other_user_key, other_app_key):
                with self.subTest(endpoint=endpoint, key=key):
                    payload = dict(data)
                    if key is not None:
                        payload["user_skey"] = key
                    rv = self.app.post("/1.0/reviews/api/" + endpoint, json=payload)
                    self.assertEqual(rv.status_code, 400)
                    self.assertFalse(rv.get_json()["success"])
                    self.assertIn("user_skey", rv.get_json()["msg"])

        # Fetch only when interacting, and use the actual server-issued key.
        item = self._review_fetch().get_json()[0]
        self.assertEqual(item["karma_up"], 0)
        self.assertEqual(item["karma_down"], 0)
        self.assertEqual(item["reported"], 0)
        self.assertNotIn("vote_id", item)
        data["user_skey"] = item["user_skey"]
        rv = self.app.post("/1.0/reviews/api/upvote", json=data)
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(rv.get_json()["success"])

        # Anonymous responses omit vote markers, but do not reset vote tracking.
        self.assertNotIn("vote_id", self._review_fetch(anonymous=True).get_json()[0])
        rv = self.app.post("/1.0/reviews/api/upvote", json=data)
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.get_json()["msg"], "already voted on this app")
        item = self._review_fetch().get_json()[0]
        self.assertEqual(item["karma_up"], 1)
        self.assertEqual(item["vote_id"], 1)

        rv = self.app.post("/1.0/reviews/api/remove", json=data)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self._review_fetch(anonymous=True).get_json(), [])

    def test_api_fetch_anonymous_preserves_bans(self):
        self.review_submit(user_hash="2" * 40)
        self.login()
        rv = self.app.get(
            "/admin/user_ban/{}".format(self.user_hash), follow_redirects=True
        )
        self.assertIn(b"Banned user", rv.data)
        self.logout()

        self.assertEqual(len(self._review_fetch(anonymous=True).get_json()), 1)
        item = self._review_fetch().get_json()[0]
        data = {
            "app_id": item["app_id"],
            "review_id": item["review_id"],
            "user_hash": self.user_hash,
            "user_skey": item["user_skey"],
        }
        for endpoint in ("upvote", "downvote", "report", "dismiss"):
            with self.subTest(endpoint=endpoint):
                rv = self.app.post("/1.0/reviews/api/" + endpoint, json=data)
                self.assertEqual(rv.status_code, 400)
                self.assertEqual(rv.get_json()["msg"], "account has been disabled due to abuse")
        rv = self._review_submit(app_id="gimp.desktop")
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.get_json()["msg"], "account has been disabled due to abuse")

    def test_api_fetch_no_results(self):

        # get the skey back for an app with no reviews
        rv = self._review_fetch(app_id="not-going-to-exist.desktop")
        assert b"An essential part of my daily workflow" not in rv.data, rv.data
        assert b"user_skey" in rv.data, rv.data

    def test_api_fetch_compat_id(self):

        self.review_submit()

        # get the reviews back for the app using compat IDs
        rv = self._review_fetch(app_id="foo.desktop", compat_ids=["inkscape.desktop"])
        assert b"An essential part of my daily workflow" in rv.data, rv.data
        assert b"user_skey" in rv.data, rv.data
        self.assertEqual(rv.get_json()[0]["app_id"], "inkscape.desktop")
        self.assertEqual(
            rv.get_json()[0]["user_skey"], _get_user_key(self.user_hash, "inkscape.desktop")
        )

    def review_upvote(self, user_hash=None):
        if not user_hash:
            user_hash = self.user_hash
        data = {
            "review_id": 1,
            "app_id": "inkscape.desktop",
            "user_hash": user_hash,
            "user_skey": _get_user_key(user_hash, "inkscape.desktop"),
        }
        return self.app.post("/1.0/reviews/api/upvote", data=json.dumps(data))

    def review_report(self, user_hash=None):
        if not user_hash:
            user_hash = self.user_hash
        data = {
            "review_id": 1,
            "app_id": "inkscape.desktop",
            "user_hash": user_hash,
            "user_skey": _get_user_key(user_hash, "inkscape.desktop"),
        }
        return self.app.post("/1.0/reviews/api/report", data=json.dumps(data))

    def test_api_upvote(self):

        # does not exist
        rv = self.review_upvote()
        assert b"invalid review ID" in rv.data, rv.data

        # first upvote
        self.review_submit()
        rv = self.review_upvote()
        assert b'success": true' in rv.data, rv.data
        assert b"voted #1 1" in rv.data, rv.data

        # duplicate upvote
        rv = self.review_upvote()
        assert b'success": false' in rv.data, rv.data
        assert b"already voted on this app" in rv.data, rv.data

        # check vote_id is set
        rv = self._review_fetch(app_id="inkscape.desktop")
        assert b'vote_id": 1' in rv.data, rv.data

        # delete review, hopefully deleting vote too
        rv = self._api_review_delete()
        assert b"removed review #1" in rv.data, rv.data
        self.run_cron_auto_delete()
        rv = self._review_fetch(app_id="inkscape.desktop")
        assert b"vote_id" not in rv.data, rv.data

    def test_api_report(self):

        # submit and verify
        self.review_submit()
        self.review_fetch()

        # should not appear again
        rv = self.review_report()
        assert b'success": true' in rv.data, rv.data
        assert b"voted #1 -5" in rv.data, rv.data
        rv = self.review_report(user_hash="729342d6a7c477bb1ea0186f8c60804a3d783183")
        assert b'success": true' in rv.data, rv.data
        assert b"voted #1 -5" in rv.data, rv.data
        rv = self._review_fetch(app_id="inkscape.desktop")
        assert b"An essential part of my daily workflow" not in rv.data, rv.data

        # duplicate upvote
        rv = self.review_upvote()
        assert b'success": false' in rv.data, rv.data
        assert b"already voted on this app" in rv.data, rv.data

    def test_api_app_rating(self):

        # nothing
        rv = self.app.get("/1.0/reviews/api/ratings/not-going-to-exist.desktop")
        assert rv.data == b"[]", rv.data

        # something
        self.review_submit()
        rv = self.app.get("/1.0/reviews/api/ratings/inkscape.desktop")
        assert b'star1": 0' in rv.data, rv.data
        assert b'star5": 1' in rv.data, rv.data
        assert b'total": 1' in rv.data, rv.data

        # all
        self.review_submit(user_hash="0000000000000000000000000000000000000000")
        rv = self.app.get("/1.0/reviews/api/ratings")
        assert b"inkscape.desktop" in rv.data, rv.data
        assert b'star1": 0' in rv.data, rv.data
        assert b'star5": 2' in rv.data, rv.data
        assert b'total": 2' in rv.data, rv.data

    def _api_review_delete(self):
        data = {
            "review_id": 1,
            "app_id": "inkscape.desktop",
            "user_hash": self.user_hash,
            "user_skey": _get_user_key(self.user_hash, "inkscape.desktop"),
        }
        return self.app.post("/1.0/reviews/api/remove", data=json.dumps(data))

    def test_api_remove(self):

        self.review_submit()

        # wrong app_id
        data = {
            "review_id": 1,
            "app_id": "dave.desktop",
            "user_hash": self.user_hash,
            "user_skey": _get_user_key(self.user_hash, "dave.desktop"),
        }
        rv = self.app.post("/1.0/reviews/api/remove", data=json.dumps(data))
        assert b"the app_id is invalid" in rv.data, rv.data

        # wrong user_hash
        data = {
            "review_id": 1,
            "app_id": "inkscape.desktop",
            "user_hash": _get_user_key(self.user_hash, "inkscape.desktop"),
            "user_skey": _get_user_key(self.user_hash, "inkscape.desktop"),
        }
        rv = self.app.post("/1.0/reviews/api/remove", data=json.dumps(data))
        assert b"no review" in rv.data, rv.data

        # wrong user_skey
        data = {
            "review_id": 1,
            "app_id": "inkscape.desktop",
            "user_hash": self.user_hash,
            "user_skey": self.user_hash,
        }
        rv = self.app.post("/1.0/reviews/api/remove", data=json.dumps(data))
        assert b"invalid user_skey" in rv.data, rv.data

        # delete a review
        rv = self._api_review_delete()
        assert b"removed review #1" in rv.data, rv.data

    def test_api_submit(self):

        # upload a report
        rv = self._review_submit()
        assert b'"success": true' in rv.data, rv.data

        # upload a 2nd report
        rv = self._review_submit(app_id="gimp.desktop")
        assert b'"success": true' in rv.data, rv.data

        # upload a duplicate report
        rv = self._review_submit()
        assert b'success": false' in rv.data, rv.data
        assert b"already reviewed this app" in rv.data, rv.data

        # upload an invalid report
        rv = self._review_submit(summary="<html>foo</html>")
        assert b'success": false' in rv.data, rv.data
        assert b"is not a valid string" in rv.data, rv.data
        rv = self._review_submit(summary="")
        assert b'success": false' in rv.data, rv.data
        assert b"missing data" in rv.data, rv.data

        # get the review back
        rv = self.app.get("/1.0/reviews/api/app/inkscape.desktop")
        assert b"Somebody Important" in rv.data, rv.data
        assert b"An essential part of my daily workflow" in rv.data, rv.data
        assert b"user_skey" not in rv.data, rv.data

        # get the review back with skey
        rv = self.app.get(
            f"/1.0/reviews/api/app/inkscape.desktop/{self.user_hash}"
        )
        assert b"An essential part of my daily workflow" in rv.data, rv.data
        assert b"user_skey" in rv.data, rv.data

        # get the reviews back for the app
        rv = self._review_fetch(distro="Ubuntu", version="1.2.4")
        assert b"An essential part of my daily workflow" in rv.data, rv.data
        assert b"user_skey" in rv.data, rv.data

    def test_fail_when_login_required(self):

        # all these are an error when not logged in
        uris = [
            "/admin/graph_month",
            "/admin/graph_year",
            "/admin/stats",
            "/admin/user_ban/1",
            "/admin/show/reported",
            "/admin/stats",
            "/admin/moderators/all",
        ]
        for uri in uris:
            rv = self.app.get(uri, follow_redirects=True)
            assert b"favicon.ico" in rv.data, rv.data
            assert b"Please log in to access this page" in rv.data, (uri, rv.data)

        # POST only
        uris = ["/admin/modify/1"]
        for uri in uris:
            rv = self.app.post(uri, follow_redirects=True)
            assert b"favicon.ico" in rv.data, rv.data
            assert b"Please log in to access this page" in rv.data, rv.data


if __name__ == "__main__":
    unittest.main()
