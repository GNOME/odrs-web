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
    item['user_display'] = e[11]
    item['rating'] = int(e[12])
    if e[13]:
        item['date_deleted'] = int(e[13].strftime("%s"))
    return item

def _create_event_item(e):
    item = {}
    item['evid'] = int(e[0])
    item['date_created'] = int(e[1].strftime("%s"))
    item['user_ip'] = e[2]
    item['user_id'] = e[3]
    item['message'] = e[4]
    return item

def _create_user_item(e):
    item = {}
    item['id'] = int(e[0])
    item['date_created'] = int(e[1].strftime("%s"))
    item['date_request'] = int(e[2].strftime("%s"))
    item['user_id'] = e[3]
    item['karma'] = int(e[4])
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

        # a table for saving each review
        try:
            cur = self._db.cursor()
            cur.execute("SELECT * FROM reviews LIMIT 1;")
        except mdb.Error, e:
            sql_db = """
                CREATE TABLE reviews (
                  id INT NOT NULL AUTO_INCREMENT,
                  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  date_deleted TIMESTAMP,
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
                  reported INT DEFAULT 0,
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
                ALTER TABLE reviews ADD reported INT DEFAULT 0;
            """
            cur.execute(sql_db)
        except mdb.Error, e:
            pass
        try:
            sql_db = """
                ALTER TABLE reviews ADD date_deleted TIMESTAMP;
            """
            cur.execute(sql_db)
        except mdb.Error, e:
            pass

        # a table for how a user has voted
        try:
            cur = self._db.cursor()
            cur.execute("SELECT * FROM votes LIMIT 1;")
        except mdb.Error, e:
            sql_db = """
                CREATE TABLE votes (
                  id INT NOT NULL AUTO_INCREMENT,
                  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  user_id TEXT DEFAULT NULL,
                  val INT DEFAULT 0,
                  dbid INT DEFAULT 0,
                  UNIQUE KEY id (id)
                ) CHARSET=utf8;
            """
            cur.execute(sql_db)

        # FIXME: remove after a few days
        try:
            sql_db = """
                ALTER TABLE votes ADD val INT DEFAULT 0;
            """
            cur.execute(sql_db)
        except mdb.Error, e:
            pass

        # a table for a specific user
        try:
            cur = self._db.cursor()
            cur.execute("SELECT * FROM users2 LIMIT 1;")
        except mdb.Error, e:
            sql_db = """
                CREATE TABLE users2 (
                  id INT NOT NULL AUTO_INCREMENT,
                  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  date_request TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  user_id TEXT DEFAULT NULL,
                  karma INT DEFAULT 0,
                  UNIQUE KEY id (id)
                ) CHARSET=utf8;
            """
            cur.execute(sql_db)

        # a table for an admin event log
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

    def review_add(self, item, user_addr):
        try:
            cur = self._db.cursor()
            cur.execute("INSERT INTO reviews (appid, locale, summary, "
                        "description, user_id, user_display, version, "
                        "distro, rating, user_addr) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                        (item['appid'],
                         item['locale'],
                         item['summary'],
                         item['description'],
                         item['user_id'],
                         item['user_display'],
                         item['version'],
                         item['distro'],
                         item['rating'],
                         user_addr,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def review_remove(self, dbid, user_id):
        """ Marks a review as removed """
        try:
            cur = self._db.cursor()
            cur.execute("UPDATE reviews SET date_deleted = CURRENT_TIMESTAMP "
                        "WHERE user_id = %s AND id = %s;",
                        (user_id, dbid,))
        except mdb.Error, e:
            raise CursorError(cur, e)
        return True

    def review_get_for_appid(self, appid):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id, date_created, appid, locale, summary, "
                        "description, version, distro, karma_up, karma_down, "
                        "user_id, user_display, rating, date_deleted "
                        "FROM reviews WHERE appid=%s AND reported=0 AND "
                        "date_deleted=0 ORDER BY date_created DESC;",
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

    def review_exists(self, item):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id FROM reviews WHERE appid=%s "
                        "AND user_id=%s AND date_deleted=0;",
                        (item['appid'], item['user_id'],))
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchone()
        if res is not None:
            return True
        return False

    def vote_exists(self, dbid, user_id):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT date_created "
                        "FROM votes WHERE dbid=%s AND user_id=%s;",
                        (dbid, user_id,))
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchone()
        if res is not None:
            return True
        return False

    def vote_add(self, dbid, val, user_id):
        """ Votes on a specific review and add to the votes database """
        try:
            cur = self._db.cursor()
            if val > 0:
                cur.execute("UPDATE reviews SET karma_up = karma_up + 1 "
                            "WHERE id = %s;", (dbid,))
            elif val < 0:
                cur.execute("UPDATE reviews SET karma_down = karma_down + 1 "
                            "WHERE id = %s;", (dbid,))
            else:
                cur.execute("UPDATE reviews SET reported = reported + 1 "
                            "WHERE id = %s;", (dbid,))
            cur.execute("INSERT INTO votes (user_id, dbid, val) "
                        "VALUES (%s, %s, %s);",
                        (user_id, dbid, val,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def review_get_all(self):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id, date_created, appid, locale, summary, "
                        "description, version, distro, karma_up, karma_down, "
                        "user_id, user_display, rating, date_deleted FROM reviews "
                        "WHERE reported=0 "
                        "ORDER BY date_created DESC;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        if not res:
            return []
        items = []
        for e in res:
            items.append(_create_review_item(e))
        return items

    def event_add(self, user_ip=None, user_id=None, message=None):
        try:
            cur = self._db.cursor()
            cur.execute("INSERT INTO eventlog2 (user_ip, user_id, message) "
                        "VALUES (%s, %s, %s);",
                        (user_ip, user_id, message,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def event_get_all(self):
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

    def user_add(self, user_id=None):
        try:
            cur = self._db.cursor()
            cur.execute("INSERT INTO users2 (user_id) VALUES (%s);",
                        (user_id,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def user_get_all(self):
        """ Get all the users on the system """
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id, date_created, date_request, user_id, karma "
                        "FROM users2 ORDER BY id DESC;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        if not res:
            return []
        items = []
        for e in res:
            items.append(_create_user_item(e))
        return items

    def user_get_by_id(self, user_id):
        """ Get information about a specific user """
        try:
            cur = self._db.cursor()
            cur.execute("SELECT id, date_created, date_request, user_id, karma "
                        "FROM users2 WHERE user_id=%s ORDER BY id DESC;",
                        (user_id,))
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchone()
        if not res:
            return None
        return _create_user_item(res)

    def user_update_request(self, user_id):
        """ Update the request time for a specific user ID """

        # if not existing, create it
        user = self.user_get_by_id(user_id)
        if not user:
            self.user_add(user_id)
            return

        # update the timestamp
        try:
            cur = self._db.cursor()
            cur.execute("UPDATE users2 SET date_request = CURRENT_TIMESTAMP "
                        "WHERE user_id = %s;", (user_id,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def user_update_karma(self, user_id, val):
        """ Update the request time for a specific user ID """

        # if not existing, create it
        user = self.user_get_by_id(user_id)
        if not user:
            self.user_add(user_id)
            return

        # update the karma value
        try:
            cur = self._db.cursor()
            cur.execute("UPDATE users2 SET karma = karma + %s "
                        "WHERE user_id = %s;", (user_id, val,))
        except mdb.Error, e:
            raise CursorError(cur, e)

    def reviews_get_rating_for_appid(self, appid):
        try:
            cur = self._db.cursor()
            cur.execute("SELECT COUNT(*) total,"
                        "       SUM(rating = 0) star0,"
                        "       SUM(rating = 20) star1,"
                        "       SUM(rating = 40) star2,"
                        "       SUM(rating = 60) star3,"
                        "       SUM(rating = 80) star4,"
                        "       SUM(rating = 100) star5 "
                        "FROM reviews WHERE appid = %s "
                        "AND date_deleted=0;", (appid,))
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchone()
        if not res:
            return []
        item = {}
        item['total'] = int(res[0])
        item['star0'] = int(res[1])
        item['star1'] = int(res[2])
        item['star2'] = int(res[3])
        item['star3'] = int(res[4])
        item['star4'] = int(res[5])
        item['star5'] = int(res[6])
        return item

    def get_stats(self):
        item = {}

        # get the total number of reviews
        try:
            cur = self._db.cursor()
            cur.execute("SELECT COUNT(*) FROM reviews;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        item['NumberReviews'] = int(res[0][0])

        # unique reviewers
        try:
            cur.execute("SELECT COUNT(DISTINCT(user_id)) FROM reviews;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        item['NumberUniqueReviewers'] = int(res[0][0])

        # total votes
        try:
            cur.execute("SELECT COUNT(*) FROM votes WHERE val = 1;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        item['NumberVotesUp'] = int(res[0][0])
        try:
            cur.execute("SELECT COUNT(*) FROM votes WHERE val = -1;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        item['NumberVotesDown'] = int(res[0][0])

        # unique voters
        try:
            cur.execute("SELECT COUNT(DISTINCT(user_id)) FROM votes;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        item['NumberUniqueVoters'] = int(res[0][0])

        # unique distros
        try:
            cur.execute("SELECT COUNT(DISTINCT(distro)) FROM reviews;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        item['NumberUniqueDistros'] = int(res[0][0])

        # unique distros
        try:
            cur.execute("SELECT COUNT(*) FROM reviews WHERE reported > 0;")
        except mdb.Error, e:
            raise CursorError(cur, e)
        res = cur.fetchall()
        item['NumberReviewsReported'] = int(res[0][0])

        # done
        return item
