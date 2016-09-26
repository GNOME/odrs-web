# Open Desktop Ratings Serice

A Flask web service for submitting application reviews

## How do I set up the database ##

To set up the database tables do:

    CREATE DATABASE odrs;
    CREATE USER 'test'@'localhost' IDENTIFIED BY 'test';
    USE odrs;
    GRANT ALL ON odrs.* TO 'test'@'localhost';
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

## How do I backup the data ##

You want to save the variable `ODRS_REVIEWS_SECRET` so that old review data
can be used on the new instance.

    export OPENSHIFT_NAMESPACE=xdgapp
    export OPENSHIFT_APP=apps
    rhc env list --app ${OPENSHIFT_APP} --namespace ${OPENSHIFT_NAMESPACE}
    rhc ssh --app ${OPENSHIFT_APP} --namespace ${OPENSHIFT_NAMESPACE}
    mysqldump -h $OPENSHIFT_MYSQL_DB_HOST \
              -P ${OPENSHIFT_MYSQL_DB_PORT:-3306} \
              -u ${OPENSHIFT_MYSQL_DB_USERNAME:-'admin'} \
              --password="$OPENSHIFT_MYSQL_DB_PASSWORD" \
              odrs > app-root/data/backup-`date +%Y%m%d`.sql
    exit
    rhc scp --app ${OPENSHIFT_APP} \
            --namespace ${OPENSHIFT_NAMESPACE} \
            download . app-root/data/backup-`date +%Y%m%d`.sql

## How do I restore from a backup ##

If this is a fresh instance you want to set up using:

    export OPENSHIFT_NAMESPACE=xdgapp
    export OPENSHIFT_APP=apps
    rhc delete-app --app ${OPENSHIFT_APP} --namespace ${OPENSHIFT_NAMESPACE}
    rhc create-app --type python-3.3 --scaling \
        --app ${OPENSHIFT_APP} --namespace ${OPENSHIFT_NAMESPACE} \
        --from-code https://github.com/hughsie/odrs-website.git
    rhc cartridge add --app ${OPENSHIFT_APP} \
        --namespace ${OPENSHIFT_NAMESPACE} \
        mysql-5.5
    rhc env set --app ${OPENSHIFT_APP} \
        --namespace ${OPENSHIFT_NAMESPACE} \
        ODRS_REVIEWS_SECRET=foobar
    rhc show-app --app ${OPENSHIFT_APP} --namespace ${OPENSHIFT_NAMESPACE}
    rhc scp --app ${OPENSHIFT_APP} --namespace ${OPENSHIFT_NAMESPACE} \
        upload backup.sql app-root/data
    rhc ssh --app ${OPENSHIFT_APP} --namespace ${OPENSHIFT_NAMESPACE}

Then restore the data with:

    mysql
      CREATE DATABASE odrs;
      use odrs;
      source app-root/data/backup.sql;

## Can I clean up the event log a bit? ##

    mysql
      DELETE FROM eventlog WHERE message = 'already reviewed';
      DELETE FROM eventlog WHERE message = 'duplicate vote';
      DELETE FROM eventlog WHERE message = 'getting';

## How to I use distro packages ##

    pkcon install python3-PyMySQL python3-flask python3-flask-wtf \
      python3-flask-login

## I have a question

Email me or grab me on IRC (`hughsie@freenode`).
