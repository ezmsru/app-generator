FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/python:3.12-slim-bookworm AS builder

USER 0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

RUN --mount=type=secret,id=usr \
    --mount=type=secret,id=tok \
    usr=$(cat /run/secrets/usr) && tok=$(cat /run/secrets/tok) && \
    pip3 config set global.index-url \
      "https://${usr}:${tok}@unixrepo.megafon.ru/artifactory/api/pypi/itbigdata-main-pypi/simple" && \
    python -m venv /opt/venv

WORKDIR /data/app
COPY ./app/requirements.txt /data/app/requirements.txt

RUN --mount=type=secret,id=usr \
    --mount=type=secret,id=tok \
    usr=$(cat /run/secrets/usr) && tok=$(cat /run/secrets/tok) && \
    /opt/venv/bin/pip install --no-cache-dir \
      --index-url "https://${usr}:${tok}@unixrepo.megafon.ru/artifactory/api/pypi/itbigdata-main-pypi/simple" \
      -r requirements.txt

COPY ./app /data/app


FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /data/app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /data/app /data/app
COPY ${WORKSPACE}/cicd-conf/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod a+x /usr/local/bin/entrypoint.sh && chown -R 11200 /data/app
USER 11200

EXPOSE {{SERVICE_PORT}}
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:{{SERVICE_PORT}}", "app:create_app()"]
