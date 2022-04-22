FROM registry.access.redhat.com/ubi8/python-38

USER 0
ADD app_data /tmp/src
RUN /usr/bin/fix-permissions /tmp/src

USER 1001
RUN /usr/libexec/s2i/assemble

ENV ODRS_HOME=/opt/app-root/src \
    LANG=C

ADD entrypoint /entrypoint
CMD /entrypoint
