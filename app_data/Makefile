# Copyright (C) 2019 Richard Hughes <richard@hughsie.com>
# SPDX-License-Identifier: GPL-2.0+

VENV=./env
PYTHON=$(VENV)/bin/python
PYTEST=$(VENV)/bin/pytest
FLASK=$(VENV)/bin/flask

setup: requirements.txt
	virtualenv ./env
	$(VENV)/bin/pip install -r requirements.txt

clean:
	rm -rf ./build
	rm -rf ./htmlcov

run:
	ODRS_REVIEWS_SECRET=1 \
	FLASK_APP=odrs/__init__.py \
	HOME=/home/hughsie/Code/odrs-web/app_data \
	$(VENV)/bin/flask run
	#FLASK_DEBUG=1

dbup:
	ODRS_CONFIG=example.cfg \
	FLASK_APP=odrs/__init__.py \
	$(FLASK) db upgrade

dbdown:
	ODRS_CONFIG=example.cfg \
	FLASK_APP=odrs/__init__.py \
	$(FLASK) db downgrade

dbmigrate:
	ODRS_CONFIG=example.cfg \
	FLASK_APP=odrs/__init__.py \
	$(FLASK) db migrate

check: $(PYTEST)
	$(PYTEST) \
		--cov=odrs \
		--cov-report=html
	$(PYTHON) ./pylint_test.py
