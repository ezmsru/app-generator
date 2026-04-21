# App Generator

Конвейер для генерации шаблонных приложений Python/Java/Node с автоматическим созданием GitLab-репозитория, наполнением шаблоном, Helm-конфигом и регистрацией в ядре.

## Структура

```
generator/
├── .gitlab-ci.yml           # Основной pipeline
├── middle/                  # Шаблоны приложений
│   ├── python-fastapi/
│   ├── python-flask/
│   ├── python-gunicorn/
│   ├── java/
│   └── node/
└── middleconf/              # Конфигурации для деплоя
    ├── python-fastapi/Dockerfile
    ├── python-flask/Dockerfile
    ├── python-gunicorn/Dockerfile
    ├── java/Dockerfile
    ├── node/Dockerfile
    └── helm-base/           # Helm chart (общий)
        ├── Chart.yaml
        ├── values.yaml
        ├── vlg-t2-dc-s-values.yaml      # DC-стенд (dev)
        ├── vlg-t2-dc-l-values.yaml      # DC-стенд (preprod)
        ├── msk-p1-dm-gen-values.yaml    # DC-стенд (prod)
        ├── msk-p1-kb-gen-values.yaml    # DC-стенд (prod-реплика)
        └── templates/
```

## Настройка

В **Settings → CI/CD → Variables** добавить:

| Переменная | Тип | Описание |
|---|---|---|
| `GITLAB_TUZ_TOKEN` | Masked, Protected | Токен ТУЗа со скоупами `api`, `write_repository` |

## Запуск

**CI/CD → Pipelines → Run Pipeline**, заполнить параметры:

- `TARGET_GROUP_NAME` — группа-продукт; создастся одновременно в `middle/itbigdata/` и `middleconf/itbigdata/`, если отсутствует
- `PROJECT_NAME` — имя нового проекта (создаётся по одному репо в каждой из двух групп)
- `TEMPLATE_TYPE` — тип шаблона (python-fastapi / python-flask / python-gunicorn / java / node)
- `DEPLOY_STANDS` — стенды (dev / dev,preprod / dev,preprod,prod)
- `HELM_STANDS_DEV`, `HELM_STANDS_PROD` — DC-стенды для helm (comma-separated), допустимые значения: `vlg-t2-dc-s`, `vlg-t2-dc-l`, `msk-p1-dm-gen`, `msk-p1-kb-gen`
- `PG_ENABLED`, `PG_HOST`, `PG_DB` — PostgreSQL
- `CH_ENABLED`, `CH_HOST`, `CH_DB` — ClickHouse
- `REDIS_ENABLED`, `REDIS_HOST` — Redis
- `WEBHOOK_URL` — опционально, URL вебхука
- `CORE_REPO_PATH` — опционально, `group/core-registry` для регистрации

## Что делает pipeline

1. **validate** — проверка имени, резолв/создание обеих групп (`middle/itbigdata/<group>` и `middleconf/itbigdata/<group>`), проверка что проект не существует ни в одной
2. **create-repo** — создание **двух** репозиториев: app в `middle/...` и config в `middleconf/...`
3. **fill-template** — копирование шаблона из `middle/<template>/` в **middle-репозиторий** (приложение)
4. **fill-config** — Dockerfile + Helm chart из `middleconf/` в **middleconf-репозиторий** (конфигурация); копируются только те `<dc>-values.yaml`, которые перечислены в `HELM_STANDS_DEV`/`HELM_STANDS_PROD` для выбранных сред
5. **setup-webhook** — webhook на оба репозитория (если указан `WEBHOOK_URL`)
6. **register** — запись в `services.yaml` ядра: `repo_url` = middle, `config_repo_url` = middleconf (если указан `CORE_REPO_PATH`)
