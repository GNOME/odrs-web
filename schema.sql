CREATE TABLE reviews (
  review_id INT NOT NULL AUTO_INCREMENT,
  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_deleted TIMESTAMP,
  app_id TEXT DEFAULT NULL,
  locale TEXT DEFAULT NULL,
  summary TEXT DEFAULT NULL,
  description TEXT DEFAULT NULL,
  user_hash TEXT DEFAULT NULL,
  user_addr TEXT DEFAULT NULL,
  user_display TEXT DEFAULT NULL,
  version TEXT DEFAULT NULL,
  distro TEXT DEFAULT NULL,
  rating INT DEFAULT 0,
  karma_up INT DEFAULT 0,
  karma_down INT DEFAULT 0,
  reported INT DEFAULT 0,
  UNIQUE KEY id (review_id)
) CHARSET=utf8;
CREATE TABLE votes (
  vote_id INT NOT NULL AUTO_INCREMENT,
  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  user_hash TEXT DEFAULT NULL,
  val INT DEFAULT 0,
  review_id INT DEFAULT 0,
  UNIQUE KEY id (vote_id)
) CHARSET=utf8;
CREATE TABLE users (
  user_id INT NOT NULL AUTO_INCREMENT,
  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  user_hash TEXT DEFAULT NULL,
  karma INT DEFAULT 0,
  is_banned INT DEFAULT 0,
  password TEXT DEFAULT NULL,
  UNIQUE KEY id (user_id)
) CHARSET=utf8;
CREATE TABLE eventlog (
  eventlog_id INT NOT NULL AUTO_INCREMENT,
  date_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  user_addr TEXT DEFAULT NULL,
  user_hash TEXT DEFAULT NULL,
  app_id TEXT DEFAULT NULL,
  important INT DEFAULT 0,
  message TEXT DEFAULT NULL,
  UNIQUE KEY id (eventlog_id)
) CHARSET=utf8;
CREATE TABLE analytics (
  datestr INT DEFAULT 0,
  app_id VARCHAR(64) DEFAULT NULL,
  fetch_cnt INT DEFAULT 1,
  UNIQUE (datestr,app_id)
) CHARSET=utf8;
CREATE INDEX date_created_idx ON eventlog (date_created);
