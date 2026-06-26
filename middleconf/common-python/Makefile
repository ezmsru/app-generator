.PHONY: installUv testEnv lintRuffBlack pytest unitTests buildApp dev-attach dev-test clean-pyc help

CURRENT_PWD := $(shell pwd)
HOME := ${CURRENT_PWD}
PYTHONPATH := ${CURRENT_PWD}:${CURRENT_PWD}/app:${PYTHONPATH}
PATH := ${CURRENT_PWD}/.uv-bin/bin:${CURRENT_PWD}:${CURRENT_PWD}/app:${PATH}

dev-attach: BASE_DOCKER_IMAGE := $(shell head -1 Dockerfile | sed -r 's/FROM\s*(.*?)\s*/\1/gi')
dev-attach: UID := $(shell id -u)
dev-attach: GID := $(shell id -g)

export

UV_RUN = UV_INDEX_ITBIGDATA_MAIN_PYPI_USERNAME=${USER} UV_INDEX_ITBIGDATA_MAIN_PYPI_PASSWORD=${PASSWORD} uv run

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

installUv:
	pip3 config set global.index-url https://${USER}:${PASSWORD}@unixrepo.megafon.ru/artifactory/api/pypi/itbigdata-main-pypi/simple
	@command -v uv >/dev/null 2>&1 || pip3 install --no-input --trusted-host unixrepo.megafon.ru --target ${CURRENT_PWD}/.uv-bin uv

testEnv: installUv
	@echo "Installing deps via uv sync"
	@if [ -f pyproject.toml ]; then \
	  UV_INDEX_ITBIGDATA_MAIN_PYPI_USERNAME=${USER} UV_INDEX_ITBIGDATA_MAIN_PYPI_PASSWORD=${PASSWORD} uv sync; \
	else \
	  echo "pyproject.toml не найден — установка зависимостей пропущена"; \
	fi

# Тесты и линт на старте не нужны — отключены (no-op)
lintRuffBlack:
	@echo "lint отключён"

pytest:
	@echo "тесты отключены"

unitTests:
	@echo "тесты отключены"

# buildApp складывает ВСЕ файлы для финального docker image в srcDirectory (app).
# Библиотека вызывает этот таргет на стадии BuildApp; Dockerfile берёт код из ./app.
# Универсально для всех python-шаблонов: исходники всегда в project/, а манифест
# зависимостей — либо pyproject.toml (uv, fastapi), либо requirements.txt (flask/gunicorn).
buildApp:
	mkdir -p ${CURRENT_PWD}/app
	cp -r ${CURRENT_PWD}/project ${CURRENT_PWD}/app/
	[ -f ${CURRENT_PWD}/pyproject.toml ] && cp ${CURRENT_PWD}/pyproject.toml ${CURRENT_PWD}/app/ || true
	[ -f ${CURRENT_PWD}/requirements.txt ] && cp ${CURRENT_PWD}/requirements.txt ${CURRENT_PWD}/app/ || true

dev-attach:
	docker pull ${BASE_DOCKER_IMAGE}
	docker run --rm -ti -u ${UID}:${GID} -v ${CURRENT_PWD}:${CURRENT_PWD} -w ${CURRENT_PWD} ${BASE_DOCKER_IMAGE} bash

dev-test: unitTests
	@echo Test complete

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'
