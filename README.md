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
| `GITLAB_TUZ_TOKEN` | Masked, Protected | Токен ТУЗа для `middle/itbigdata` (скоупы `api`, `write_repository`) |
| `GITLAB_MIDDLECONF_TUZ_TOKEN` | Masked, Protected | Токен ТУЗа для `middleconf/itbigdata` (скоупы `api`, `write_repository`) |
| `DELETE_PASSWORD` | Masked | Пароль подтверждения для режима удаления. Без неё удаление запрещено |

## Запуск

Параметры заданы через типизированные [`spec:inputs`](https://docs.gitlab.com/ci/inputs/) (GitLab ≥ 17.7) — при **CI/CD → Pipelines → Run pipeline** GitLab покажет форму с дропдаунами, чекбоксами и валидацией. Pipeline создаётся **только вручную** (`workflow: $CI_PIPELINE_SOURCE == "web"`), поэтому `git push` в этот репозиторий pipeline не порождает.

| Input | Тип | По умолчанию | Описание |
|---|---|---|---|
| `action` | options | `create` | режим: `create` — создать репозитории; `delete` — удалить (нужен `delete_password`) |
| `project_name` | string, **required**, regex `^[a-z0-9][a-z0-9._-]*$` | — | **цель** (для обоих режимов): имя репо. `create` — создаётся; `delete` — удаляется |
| `target_group_name` | string, regex | `cicdbigdata` | **цель** (для обоих режимов): группа-продукт в `middle/itbigdata/` и `middleconf/itbigdata/`. `create` — создастся, если нет; `delete` — группа удаляемого репо (сама **не** удаляется) |
| `template_type` | options | `python-fastapi` | python-fastapi / python-flask / python-gunicorn / java / node |
| `deploy_stands` | options | `dev` | dev / dev,preprod / dev,preprod,prod |
| `helm_stands_dev` | options | `vlg-t2-dc-s` | DC-стенды для dev/preprod: `vlg-t2-dc-s`, `vlg-t2-dc-l` (или оба) |
| `helm_stands_prod` | options | `msk-p1-dm-gen` | DC-стенды для prod: `msk-p1-dm-gen`, `msk-p1-kb-gen` (или оба) |
| `pam_source` | string | `""` | путь до секретов в PAM (например: `LLM/cost_scan`) |
| `pg_enabled` / `pg_host` / `pg_db` | boolean / string | `false` / `""` | PostgreSQL |
| `ch_enabled` / `ch_host` / `ch_db` | boolean / string | `false` / `""` | ClickHouse |
| `redis_enabled` / `redis_host` | boolean / string | `false` / `""` | Redis |
| `s3_enabled` / `s3_endpoint_url` / `s3_bucket` / `s3_prefix` | boolean / string | `false` / `""` | S3 (токен доступа — из PAM: `<project_name>_s3_token`) |
| `servicemonitor_enabled` | boolean | `false` | ServiceMonitor для Prometheus. При `true` → `serviceMonitor.enabled=true` в values; манифест из `templates/servicemonitor.yaml` (scrape `/eapi/<app>/manage/prometheus`) |
| `core_repo_path` | string | `""` | `group/core-registry` для регистрации (пусто — не регистрировать) |
| `product_name` | string | `""` | имя продукта для job-dsl (пусто — взять `project_name`) |
| `delete_password` | string | `""` | пароль подтверждения удаления (нужен при `action=delete`; сверяется с masked-переменной `DELETE_PASSWORD`) |

> Включённые (`*_enabled=true`) интеграции БД/Redis/S3 попадают в helm-values; выключенные — вырезаются целиком (вместе с PAM-секретом) на стадии `fill-config`, чтобы под не падал на отсутствующем секрете. Если `*_enabled=true`, соответствующие host/db обязательны — это проверяется в `validate-params`.

## Что делает pipeline

Порядок стадий: `validate → create-repo → register-dsl → fill-config → fill-template → setup-webhook → register`.

1. **validate-params** — проверка имени (regex) и зависимостей (`*_enabled=true ⇒ host/db обязательны`), резолв/создание обеих групп (`middle/itbigdata/<group>` и `middleconf/itbigdata/<group>`), проверка что проект не существует ни в одной
2. **create-repo** — создание **двух** репозиториев: app в `middle/...` и config в `middleconf/...`
3. **register-in-dsl** — регистрация продукта в `nmf-job-dsl` (`middle/itbigdata/<product>.yaml`) через ruamel.yaml + автоматический MR
4. **fill-config** — Dockerfile + Helm chart из `middleconf/` в **middleconf-репозиторий**; копируются только те `<dc>-values.yaml`, которые перечислены в `helm_stands_dev`/`helm_stands_prod` для выбранных сред; неиспользуемые интеграции (`*_enabled != true`) вырезаются из values по маркерам
5. **fill-template** — копирование шаблона из `middle/<template>/` в **middle-репозиторий** (ветка `develop` + тег `0.0.1`)
6. **setup-webhook** — webhook на **middle-репозиторий** (URL задан в job)
7. **register-in-core** — запись в `services.yaml` ядра: `repo_url` = middle, `config_repo_url` = middleconf (если указан `core_repo_path`)

## Удаление репозитория

Выбери в форме `action = delete`. Цель указывается **теми же полями, что и при создании** — `project_name` + `target_group_name` (удаляешь тем же, чем создавал). Все обычные стадии исключаются (`rules: $ACTION == "create"`), выполняется только джоба **delete-repository** (стадия `delete`).

Что нужно заполнить:

| Поле | Значение |
|---|---|
| `action` | `delete` |
| `project_name` | имя удаляемого репо (как при создании) |
| `target_group_name` | группа, в которой лежит репо (по умолчанию `cicdbigdata`) |
| `delete_password` | пароль (сверяется с masked-переменной `DELETE_PASSWORD`) |

Что делает джоба:
1. Валидирует `project_name`/`target_group_name` и сверяет `delete_password` с masked CI-переменной `DELETE_PASSWORD` (если переменная не задана — удаление запрещено).
2. Печатает баннер с полными путями того, что будет удалено.
3. Удаляет проекты `middle/itbigdata/<target_group_name>/<project_name>` и `middleconf/itbigdata/<target_group_name>/<project_name>` через GitLab API.
4. Удаляет строку продукта из `nmf-job-dsl` (`middle/itbigdata/<product>.yaml`) через автоматический MR.

```
========================================
  РЕЖИМ УДАЛЕНИЯ
  middle    : middle/itbigdata/cicdbigdata/ocr_abd
  middleconf: middleconf/itbigdata/cicdbigdata/ocr_abd
  job-dsl   : middle/itbigdata/cicdbigdata.yaml → продукт "ocr_abd"
  (группа cicdbigdata НЕ удаляется)
========================================
```

> Удаляются **только** два репозитория `project_name` и запись в job-dsl. Группа `target_group_name` **не трогается** — в ней могут оставаться другие проекты. Удаление идемпотентно: уже удалённые объекты (HTTP 404) пропускаются.
