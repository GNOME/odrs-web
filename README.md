# Open Desktop Ratings Service

A Flask web service for submitting application reviews

## Setting up local environment

The easiest way is to run `docker compose up` in the root directory. This will
bring up a local ODRS instance with all needed services. Gunicorn can be
directly accessed at http://localhost:8080, while nginx that would be used for
production traffic listens at http://localhost:8000.

The entrypoint script creates a default admin user with login `admin@test.com`
and password `Pa$$w0rd`.

## Deployment

New commits to the master branch are automatically deployed to the testing
instance at https://odrs-dev.apps.openshift4.gnome.org/.

A commit can be promoted to production environment by manually starting the
`odrs` job [here](https://gitlab.gnome.org/Infrastructure/odrs-web/-/jobs).

## I have a question

Email me or grab me on IRC (`hughsie@libera.chat`).
