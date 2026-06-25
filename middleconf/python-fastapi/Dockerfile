FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/python:3.12-slim-bookworm AS builder

USER 0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT="/opt/venv" \
    UV_LINK_MODE="copy" \
    PATH="/opt/venv/bin:$PATH"

RUN \
    --mount=type=secret,id=usr \
    --mount=type=secret,id=tok \
    user_var="$(cat /run/secrets/usr)" \
    token_var="$(cat /run/secrets/tok)" && \
    pip3 install --no-cache-dir uv \
    --index-url=https://${user_var}:${token_var}@unixrepo.megafon.ru/artifactory/api/pypi/itbigdata-main-pypi/simple

WORKDIR /data/app

# srcDirectory = ./app (наполняется make-таргетом buildApp): там pyproject.toml
# и каталог project/ с модулями приложения.
COPY ./app/pyproject.toml /data/app/pyproject.toml

RUN \
    --mount=type=secret,id=usr \
    --mount=type=secret,id=tok \
    user_var="$(cat /run/secrets/usr)" \
    token_var="$(cat /run/secrets/tok)" && \
    uv sync --no-install-project \
    --default-index=https://${user_var}:${token_var}@unixrepo.megafon.ru/artifactory/api/pypi/itbigdata-main-pypi/simple

# Модули кладём плоско в /data/app (project/main.py → /data/app/main.py)
COPY ./app/project/. /data/app/


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
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{{SERVICE_PORT}}"]
