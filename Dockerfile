FROM centos/httpd-24-centos7 

USER root 

RUN yum install -y gcc make \
    mariadb \
    mariadb-devel \
    python36-click \
    python36-cryptography \
    python36-dateutil \
    python36-devel \
    python36-jinja2 \
    python36-markupsafe \
    python36-pip \
    python36-PyMySQL \
    rh-python36-mod_wsgi \
    uwsgi-plugin-python36

ENV ODRS_HOME=/opt/app-root/src \
    LANG=C

RUN pip3 install --prefix=/usr \
    flask-login \
    flask-migrate \
    flask-wtf \
    mysqlclient \
    PyMySQL \
    sqlalchemy

WORKDIR ${ODRS_HOME}

COPY app_data ${ODRS_HOME}

RUN python36 /opt/app-root/src/cron.py ratings /opt/app-root/src/odrs/static/ratings.json

RUN chown -R 1000310000:0 ${ODRS_HOME} && \
    chmod -R 664 ${ODRS_HOME} && \
    find ${ODRS_HOME} -type d -exec chmod 775 {} +

EXPOSE 8443

USER 1001 
ENTRYPOINT ["/usr/bin/run-httpd"]
