FROM registry.access.redhat.com/hi/python:3.13-builder AS builder

USER 0
RUN ["dnf", "install", "-y", "mysql-devel", "libxml2-devel", "libxslt-devel"]
RUN ["dnf", "clean", "all"]
RUN ["python3", "-m", "venv", "/opt/venv"]
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN ["pip3", "install", "--no-cache-dir", "-r", "/tmp/requirements.txt"]

FROM registry.access.redhat.com/hi/python:3.13

COPY --from=builder /opt/venv /opt/venv
COPY --chown=65532:65532 . /opt/app-root/src

ENV PATH="/opt/venv/bin:$PATH" \
    ODRS_HOME=/opt/app-root/src \
    LANG=C \
    APP_MODULE=odrs:app

WORKDIR /opt/app-root/src
USER 65532
VOLUME ["/tmp/ratings"]

CMD ["python3", "/opt/app-root/src/entrypoint.py"]
