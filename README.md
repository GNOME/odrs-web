# Open Desktop Ratings Service

A Flask web service for submitting application reviews

## How do I set up the database ##

To set up the database tables do:

    CREATE DATABASE odrs;
    CREATE USER 'test'@'localhost' IDENTIFIED BY 'test';
    USE odrs;
    GRANT ALL ON odrs.* TO 'test'@'localhost';

The default admin password is `Pa$$w0rd`

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
      DELETE FROM eventlog WHERE message = 'getting moderatable reviews';
      DELETE FROM eventlog WHERE message LIKE 'voted % on review';

## How to I use distro packages ##

    pkcon install python3-PyMySQL python3-flask python3-flask-wtf \
      python3-flask-login

## I have a question

Email me or grab me on IRC (`hughsie@libera.chat`).

## How to build the docker image?

    podman build . \
        --build-arg ODRS_REVIEWS_SECRET=1 \
        --build-arg SQLALCHEMY_DATABASE_URI=mysql+pymysql://test:test@localhost/odrs?charset=utf8mb4
    podman images
    podman run --env-file env.cfg <image>
    podman run --env-file env.cfg -it --entrypoint /bin/bash <image>
