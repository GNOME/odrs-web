# Open Desktop Ratings Serice

A Flask web service for submitting application reviews

## How do I set up the database ##

To set up the database tables do:

    CREATE DATABASE odrs;
    CREATE USER 'test'@'localhost' IDENTIFIED BY 'test';
    USE odrs;
    GRANT ALL ON odrs.* TO 'test'@'localhost';
    SOURCE /path/to/schema.sql

## How do I backup the data ##

You want to save the variable `ODRS_REVIEWS_SECRET` so that old review data
can be used on the new instance.

    mysqldump odrs > backup.sql

## How do I restore from a backup ##

    mysql
      CREATE DATABASE odrs;
      use odrs;
      source backup.sql;

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
