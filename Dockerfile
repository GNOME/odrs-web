FROM centos/httpd-24-centos7 

USER root 

RUN yum update -y
RUN yum install gcc make python27-python python27-python-pip python27-mod_wsgi python27-python-devel python2-cryptography python-flask python2-flask-wtf python2-flask-login python2-PyMySQL -y

ENV ODRS_HOME=/opt/app-root/src \
    LANG=C

WORKDIR ${ODRS_HOME}

COPY app_data ${ODRS_HOME}

RUN python /opt/app-root/src/cron.py ratings /opt/app-root/src/app/static/ratings.json 

COPY entrypoint.sh /usr/local/bin
EXPOSE 8443

USER 1001 
ENTRYPOINT ["entrypoint.sh"]
