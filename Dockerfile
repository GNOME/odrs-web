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
    lxml \
    mysqlclient \
    PyMySQL \
    sqlalchemy

WORKDIR ${ODRS_HOME}

COPY app_data ${ODRS_HOME}

RUN LANG=en_US.utf8 \
    FLASK_APP=odrs/__init__.py \
    SQLALCHEMY_TRACK_MODIFICATIONS=False \
    flask db upgrade

RUN curl https://flathub.org/repo/appstream/x86_64/appstream.xml.gz -o /tmp/appstream.xml.gz

RUN python36 /opt/app-root/src/cron.py appstream-import /tmp/appstream.xml.gz

RUN curl https://raw.githubusercontent.com/hughsie/badwords/master/badwords.csv -o /tmp/badwords.csv

RUN LANG=en_US.utf8 python36 /opt/app-root/src/cron.py taboo-import /tmp/badwords.csv

RUN python36 /opt/app-root/src/cron.py ratings /opt/app-root/src/odrs/static/ratings.json

RUN chown -R 1000310000:0 ${ODRS_HOME} && \
    chmod -R 664 ${ODRS_HOME} && \
    find ${ODRS_HOME} -type d -exec chmod 775 {} +

EXPOSE 8443

USER 1001 
ENTRYPOINT ["/usr/bin/run-httpd"]
