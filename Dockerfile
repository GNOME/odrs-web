FROM centos/httpd-24-centos7 

USER root 

RUN yum install -y gcc make \
    python36-cryptography \
    python36-devel \
    python36-pip \
    python36-PyMySQL \
    uwsgi-plugin-python36

ENV ODRS_HOME=/opt/app-root/src \
    LANG=C

COPY app_data/requirements.txt /tmp/requirements.txt

RUN pip3 install --prefix=/usr -r /tmp/requirements.txt

WORKDIR ${ODRS_HOME}

COPY app_data ${ODRS_HOME}

RUN python36 /opt/app-root/src/cron.py ratings /opt/app-root/src/app/static/ratings.json

RUN chown -R 1000310000:0 ${ODRS_HOME} && \
    chmod -R 664 ${ODRS_HOME} && \
    find ${ODRS_HOME} -type d -exec chmod 775 {} +

EXPOSE 8443

USER 1001 
ENTRYPOINT ["/usr/bin/run-httpd"]
