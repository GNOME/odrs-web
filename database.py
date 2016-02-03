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

def _create_review_item(e):
    item = {}
    item['dbid'] = int(e[0])
    item['date_created'] = e[1].strftime("%s")
    item['appid'] = e[2]
    item['locale'] = e[3]
    item['summary'] = e[4]
    item['description'] = e[5]
    item['version'] = e[6]
    item['distro'] = e[7]
    item['karma'] = e[8]
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

        # test table exists
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
                  version TEXT DEFAULT NULL,
                  distro TEXT DEFAULT NULL,
                  karma INT DEFAULT 0,
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
                        "description, user_id, version, distro, user_addr) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
                        (item['appid'],
                         item['locale'],
                         item['summary'],
                         item['description'],
                         item['user_id'],
                         item['version'],
                         item['distro'],
                         user_addr,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def get_reviews_for_appid(self, appid):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id, date_created, appid, locale, summary, "
                        "description, version, distro, karma "
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

    def vote(self, dbid, val):
        try:
            cur = self._db.cursor()
            cur.execute("UPDATE reviews SET karma = karma + %s WHERE id = %s;",
                        (val, dbid,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def get_reviews(self):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id, date_created, appid, locale, summary, "
                        "description, version, distro, karma "
                        "FROM reviews ORDER BY date_created DESC;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        if not res:
            return []
        items = []
        for e in res:
            items.append(_create_review_item(e))
        return items
