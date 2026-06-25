FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/python:3.12-slim-bookworm AS builder

USER 0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT="/opt/venv" \
    UV_LINK_MODE="copy" \
    PATH="/opt/venv/bin:$PATH"

RUN --mount=type=secret,id=usr \
    --mount=type=secret,id=tok \
    usr=$(cat /run/secrets/usr) && tok=$(cat /run/secrets/tok) && \
    pip3 install --no-cache-dir uv \
      --index-url "https://${usr}:${tok}@unixrepo.megafon.ru/artifactory/api/pypi/itbigdata-main-pypi/simple"

WORKDIR /data/app

# В контексте docker-сборки код приложения лежит под ./app (корень product-репо).
COPY ./app/pyproject.toml /data/app/pyproject.toml

RUN --mount=type=secret,id=usr \
    --mount=type=secret,id=tok \
    export UV_INDEX_ITBIGDATA_MAIN_PYPI_USERNAME="$(cat /run/secrets/usr)"; \
    export UV_INDEX_ITBIGDATA_MAIN_PYPI_PASSWORD="$(cat /run/secrets/tok)"; \
    uv sync --no-install-project

COPY ./app/app /data/app/app


FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    UV_PROJECT_ENVIRONMENT="/opt/venv"

WORKDIR /data/app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /data/app /data/app
COPY ${WORKSPACE}/cicd-conf/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod a+x /usr/local/bin/entrypoint.sh && chown -R 11200 /data/app
USER 11200

EXPOSE {{SERVICE_PORT}}
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{{SERVICE_PORT}}"]
