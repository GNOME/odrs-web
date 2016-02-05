#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Richard Hughes <richard@hughsie.com>
# Licensed under the GNU General Public License Version 3

import MySQLdb as mdb
import cgi

class CursorError(Exception):
    def __init__(self, cur, e):
        self.value = cgi.escape(cur._last_executed) + '&#10145; ' + cgi.escape(str(e))
    def __str__(self):
        return repr(self.value)

def _combine_karma(karma_up, karma_down):
    """ This is required because society is broken """
    return (karma_up * 5) - karma_down

def _create_review_item(e):
    item = {}
    item['dbid'] = int(e[0])
    item['date_created'] = int(e[1].strftime("%s"))
    item['appid'] = e[2]
    item['locale'] = e[3]
    item['summary'] = e[4]
    item['description'] = e[5]
    item['version'] = e[6]
    item['distro'] = e[7]
    item['karma'] = _combine_karma(int(e[8]), int(e[9]))
    item['user_id'] = e[10]
    return item

def _create_event_item(e):
    item = {}
    item['evid'] = int(e[0])
    item['date_created'] = int(e[1].strftime("%s"))
    item['user_ip'] = e[2]
    item['user_id'] = e[3]
    item['message'] = e[4]
    return item

class ReviewsDatabase(object):

    def __init__(self, environ):
        """ Constructor for object """
        assert environ
        self._db = None
        try:
            if 'OPENSHIFT_MYSQL_DB_HOST' in environ:
                self._db = mdb.connect(environ['OPENSHIFT_MYSQL_DB_HOST'],
                                       environ['OPENSHIFT_MYSQL_DB_USERNAME'],
                                       environ['OPENSHIFT_MYSQL_DB_PASSWORD'],
                                       'secure',
                                       int(environ['OPENSHIFT_MYSQL_DB_PORT']),
                                       use_unicode=True, charset='utf8')
            else:
                # mysql -u root -p
                # CREATE DATABASE secure;
                # CREATE USER 'test'@'localhost' IDENTIFIED BY 'test';
                # USE secure;
                # GRANT ALL ON secure.* TO 'test'@'localhost';
                self._db = mdb.connect('localhost', 'test', 'test', 'secure',
                                       use_unicode=True, charset='utf8')
            self._db.autocommit(True)
        except mdb.Error as e:
            print("Error %d: %s" % (e.args[0], e.args[1]))
        assert self._db

        # test ratings table exists
        try:
            cur = self._db.cursor()
            cur.execute("SELECT * FROM reviews LIMIT 1;")
        except mdb.Error, e:
            sql_db = """
                CREATE TABLE reviews (
                  id INT NOT NULL AUTO_INCREMENT,
                  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  appid TEXT DEFAULT NULL,
                  locale TEXT DEFAULT NULL,
                  summary TEXT DEFAULT NULL,
                  description TEXT DEFAULT NULL,
                  user_id TEXT DEFAULT NULL,
                  user_addr TEXT DEFAULT NULL,
                  user_display TEXT DEFAULT NULL,
                  version TEXT DEFAULT NULL,
                  distro TEXT DEFAULT NULL,
                  rating INT DEFAULT 0,
                  karma_up INT DEFAULT 0,
                  karma_down INT DEFAULT 0,
                  UNIQUE KEY id (id)
                ) CHARSET=utf8;
            """
            cur.execute(sql_db)

        # FIXME: remove after a few days
        try:
            sql_db = """
                ALTER TABLE reviews ADD rating INT DEFAULT 0;
                ALTER TABLE reviews ADD karma_up INT DEFAULT 0;
                ALTER TABLE reviews ADD karma_down INT DEFAULT 0;
                ALTER TABLE reviews ADD user_display TEXT DEFAULT NULL;
            """
            cur.execute(sql_db)
        except mdb.Error, e:
            pass

        # test user table exists
        try:
            cur = self._db.cursor()
            cur.execute("SELECT * FROM voted LIMIT 1;")
        except mdb.Error, e:
            sql_db = """
                CREATE TABLE voted (
                  id INT NOT NULL AUTO_INCREMENT,
                  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  user_id TEXT DEFAULT NULL,
                  dbid INT,
                  UNIQUE KEY id (id)
                ) CHARSET=utf8;
            """
            cur.execute(sql_db)

        # test event log table exists
        try:
            cur = self._db.cursor()
            cur.execute("SELECT * FROM eventlog2 LIMIT 1;")
        except mdb.Error, e:
            sql_db = """
                CREATE TABLE eventlog2 (
                  id INT NOT NULL AUTO_INCREMENT,
                  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  user_ip TEXT DEFAULT NULL,
                  user_id TEXT DEFAULT NULL,
                  message TEXT DEFAULT NULL,
                  UNIQUE KEY id (id)
                ) CHARSET=utf8;
            """
            cur.execute(sql_db)

    def __del__(self):
        """ Clean up the database """
        if self._db:
            self._db.close()

    def add_app(self, item, user_addr):
        try:
            cur = self._db.cursor()
            cur.execute("INSERT INTO reviews (appid, locale, summary, "
                        "description, user_id, version, distro, user_addr, rating) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",
                        (item['appid'],
                         item['locale'],
                         item['summary'],
                         item['description'],
                         item['user_id'],
                         item['version'],
                         item['distro'],
                         user_addr,
                         item['rating'],))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def get_reviews_for_appid(self, appid):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id, date_created, appid, locale, summary, "
                        "description, version, distro, karma_up, karma_down, user_id "
                        "FROM reviews WHERE appid=%s ORDER BY date_created DESC;",
                        (appid,))
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        if not res:
            return []
        items = []
        for e in res:
            items.append(_create_review_item(e))
        return items

    def has_reviewed(self, item):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id FROM reviews WHERE appid=%s AND user_id=%s;",
                        (item['appid'], item['user_id'],))
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchone()
        if res is not None:
            return True
        return False

    def has_voted(self, dbid, user_id):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT date_created "
                        "FROM voted WHERE dbid=%s AND user_id=%s;",
                        (dbid, user_id,))
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchone()
        if res is not None:
            return True
        return False

    def vote(self, dbid, val, user_id):
        """ Votes on a specific review and add to the voted database """
        try:
            cur = self._db.cursor()
            if val > 0:
                cur.execute("UPDATE reviews SET karma_up = karma_up + 1 "
                            "WHERE id = %s;", (dbid,))
            else:
                cur.execute("UPDATE reviews SET karma_down = karma_down + 1 "
                            "WHERE id = %s;", (dbid,))
            cur.execute("INSERT INTO voted (user_id, dbid) VALUES (%s, %s);",
                        (user_id, dbid,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def get_reviews(self):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id, date_created, appid, locale, summary, "
                        "description, version, distro, karma_up, karma_down, "
                        "user_id FROM reviews ORDER BY date_created DESC;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        if not res:
            return []
        items = []
        for e in res:
            items.append(_create_review_item(e))
        return items

    def add_event(self, user_ip=None, user_id=None, message=None):
        try:
            cur = self._db.cursor()
            cur.execute("INSERT INTO eventlog2 (user_ip, user_id, message) "
                        "VALUES (%s, %s, %s);",
                        (user_ip, user_id, message,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def get_events(self):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id, date_created, user_ip, user_id, message "
                        "FROM eventlog2 ORDER BY id DESC;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        if not res:
            return []
        items = []
        for e in res:
            items.append(_create_event_item(e))
        return items

    def get_ratings(self, appid):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT COUNT(*) total,"
                        "       SUM(rating = 0) star0,"
                        "       SUM(rating = 1) star1,"
                        "       SUM(rating = 2) star2,"
                        "       SUM(rating = 3) star3,"
                        "       SUM(rating = 4) star4,"
                        "       SUM(rating = 5) star5 "
                        "FROM reviews WHERE appid = %s;", (appid,))
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        if not res:
            return []
        item = {}
        item['total'] = int(res[0][0]);
        item['star0'] = int(res[0][1]);
        item['star1'] = int(res[0][2]);
        item['star2'] = int(res[0][3]);
        item['star3'] = int(res[0][4]);
        item['star4'] = int(res[0][5]);
        item['star5'] = int(res[0][6]);
        return item
