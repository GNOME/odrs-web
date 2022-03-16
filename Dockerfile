FROM centos/httpd-24-centos7 

USER root 

RUN yum install -y gcc make \
    mariadb \
    mariadb-devel \
    python36-devel \
    python36-PyMySQL \
    rh-python36-mod_wsgi \
    uwsgi-plugin-python36

ENV ODRS_HOME=/opt/app-root/src \
    LANG=C

WORKDIR ${ODRS_HOME}

COPY app_data ${ODRS_HOME}

RUN pip3 install --prefix=/usr -r ${ODRS_HOME}/requirements.txt

RUN LANG=en_US.utf8 \
    FLASK_APP=odrs/__init__.py \
    SQLALCHEMY_TRACK_MODIFICATIONS=False \
    flask db upgrade

RUN python3 /opt/app-root/src/cron.py fsck

RUN curl https://dl.flathub.org/repo/appstream/x86_64/appstream.xml.gz -o /tmp/appstream.xml.gz

RUN python3 /opt/app-root/src/cron.py appstream-import /tmp/appstream.xml.gz

RUN curl https://raw.githubusercontent.com/hughsie/badwords/master/badwords.csv -o /tmp/badwords.csv

RUN LANG=en_US.utf8 python3 /opt/app-root/src/cron.py taboo-import /tmp/badwords.csv

RUN python3 /opt/app-root/src/cron.py ratings /opt/app-root/src/odrs/static/ratings.json
RUN cp /opt/app-root/src/odrs/static/ratings.json /opt/app-root/src/odrs/static/ratings.json.bak
RUN gzip /opt/app-root/src/odrs/static/ratings.json
RUN mv /opt/app-root/src/odrs/static/ratings.json.bak /opt/app-root/src/odrs/static/ratings.json
RUN brotli -k /opt/app-root/src/odrs/static/ratings.json

RUN chown -R 1000310000:0 ${ODRS_HOME} && \
    chmod -R 664 ${ODRS_HOME} && \
    find ${ODRS_HOME} -type d -exec chmod 775 {} +

EXPOSE 8443

USER 1001 
ENTRYPOINT ["/usr/bin/run-httpd"]
