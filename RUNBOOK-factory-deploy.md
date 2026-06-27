# Runbook: от 0 до деплоя сервиса на Фабрике Микросервисов (itbigdata)

> **Для кого:** разработчик, которому нужно завести **новый сервис в УЖЕ существующую ИС** (продукт) на Фабрике Микросервисов MegaFon и довести его до деплоя — от dev (sandbox) до prod.
>
> **Главный инструмент:** джоба-генератор (Run pipeline), которая по форме создаёт оба репозитория, регистрирует продукт в `nmf-job-dsl`, вешает webhook и автоматически выкатывает скелет приложения в dev.

## Навигация

- [0. Коротко — чек-лист «с 0 до dev»](#0-коротко--чек-лист-с-0-до-dev)
- [1. Предпосылки](#1-предпосылки-до-запуска-генератора)
- [2. Шаг 1 — Запустить джобу-генератор](#2-шаг-1--запустить-джобу-генератор)
- [3. Что генератор сделал автоматически](#3-что-генератор-сделал-автоматически)
- [4. Шаг 2 — Разработка](#4-шаг-2--разработка)
- [5. Деплой по стендам](#5-деплой-по-стендам-детально)
- [6. Ветвление (Git Flow) и версионирование](#6-ветвление-git-flow-и-версионирование-теги)
- [7. Проверка деплоя](#7-проверка-деплоя)
- [8. Troubleshooting](#8-troubleshooting)
  - [8.0 Принцип траблшутинга (слои)](#80-принцип-траблшутинга--куда-смотреть-по-слоям)
  - [8.1 Частые ошибки Фабрики](#81-частые-ошибки-сборкидеплоя-специфика-фабрики)
  - [8.2 Топ-10 ошибок Kubernetes](#82-топ-10-частых-ошибок-деплоя-в-kubernetes)
- [9. Удаление сервиса](#9-удаление-сервиса-actiondelete)
- [10. Приложения](#10-приложения)

> ℹ️ Ссылки навигации работают в GitHub/GitLab (markdown-якоря). В **Confluence** якоря генерятся иначе — там вставь макрос **Table of Contents** (`{toc}`), он построит оглавление из заголовков автоматически.

---

> ⚠️ **ПЕРЕД ПУБЛИКАЦИЕЙ В CONFLUENCE — заполнить плейсхолдеры** (помечены `<…>`):
> - `<кто-заводит-PAM>` / `<кто-заводит-namespace-квоту>` — ответственный (DevOps/владелец ИС).
> Остальное (стенды, ресурсы, PAM-пути, IS-коды, контакты DevOps, ссылка на генератор) — фактическое, ниже.
>
> **Контакт DevOps:** email `it-reporting-deployment-devops@megafon.ru`; заявки в Jira — [DATA](https://jira.megafon.ru/browse/DATA).

---

## 0. Коротко — чек-лист «с 0 до dev»

- [ ] **Предпосылки**: есть доступ Developer в `middle/itbigdata` и `middleconf/itbigdata`; ИС (продукт) уже существует; при подключении БД/Redis/S3 — заведены PAM-секреты.
- [ ] **Шаг 1.** Запустить **джобу-генератор** (Run pipeline) с `action=create`, заполнить форму.
- [ ] **Шаг 2.** Дождаться зелёного пайплайна → созданы 2 репо + продукт в job-dsl + webhook + **авто-деплой скелета в dev**.
- [ ] **Шаг 3.** Проверить деплой: джоба в Jenkins → под в Rancher (`vlg-t2-dc-s`) → health `200`.
- [ ] **Шаг 4.** Клонировать middle-репо (ветка `develop`), писать код, пушить в `develop` → авто-редеплой в dev.
- [ ] **Дальше:** preprod = MR `develop→master`; prod = принятие MR в master (см. разделы 5.2–5.3).

---

## 1. Предпосылки (до запуска генератора)

| Предпосылка | Кто обеспечивает | Комментарий |
|---|---|---|
| Доступ GitLab: **Developer** в группах `middle/itbigdata` и `middleconf/itbigdata` | DevOps (`it-reporting-deployment-devops@megafon.ru`, заявки в Jira [DATA](https://jira.megafon.ru/browse/DATA)) | Нужен, чтобы клонировать/пушить. Для **удаления** репозитория нужен **Owner**. |
| **ИС (продукт) существует** — `target_group_name` | владелец ИС | Например `cost_scan`, `llm-botforge`. Генератор создаст GitLab-подгруппу, если её нет, но сама ИС (квота namespace, label в cmdb) должна быть зарегистрирована заранее. |
| **Namespace-квота** в Rancher на ИС | `<кто-заводит-namespace-квоту>` | helm создаёт namespace при первом деплое, но **ресурсная квота** на ИС выделяется отдельно (dev/preprod: 250m/256mb на продукт). |
| **PAM-секреты** (если включаешь PG/Redis/S3) | `<кто-заводит-PAM>` | Должны лежать в SingleConnect по пути `/MegaFon/Common/Data-Analytics/<stand>/<pam_source>/`. Если интеграция включена, а секрета нет — ESO не создаст k8s Secret и **под не стартует**. |
| **CI-переменные** генератора (токены ТУЗа, `DELETE_PASSWORD` и т.п.) | DevOps (разово) | Разработчику трогать НЕ нужно — заданы на уровне проекта генератора. |
| **label `megafon.ru/informationSystem`** валиден в ФНС/cmdb | владелец ИС | Иначе деплой упадёт на kyverno-политике (см. Troubleshooting). Значение = англ. название ИС из `cmdb.megafon.ru`. |

> ℹ️ Этот runbook — про **добавление компонента в существующую ИС**. Подъём НОВОЙ ИС с нуля (регистрация в cmdb, выделение namespace-квоты, заведение PAM) выходит за рамки генератора — оформляется отдельно через DevOps (`it-reporting-deployment-devops@megafon.ru`, заявки в Jira [DATA](https://jira.megafon.ru/browse/DATA)).

---

## 2. Шаг 1 — Запустить джобу-генератор

**Где:** проект генератора [**Generator App**](https://cicd-git.megafon.ru/middle/itbigdata/devops_tools/generator-app) → в левом меню **CI/CD → Pipelines** → кнопка **▶ Запустить pipeline** (Run pipeline) → выбрать ветку → заполнить форму инпутов → нажать **▶ Запустить pipeline**.

### Поля формы (Run pipeline)

| Поле | Обяз. | Что вписать (пример для dev) | Примечание |
|---|---|---|---|
| `action` | да | `create` | `create` — создать сервис; `delete` — удалить (см. раздел 9). |
| `project_name` | **да** | `cost-scan-api` | Имя репозитория/компонента. Только `a-z 0-9 . _ -`, без пробелов. Создаётся в обоих репо. |
| `target_group_name` | **да** | `cost_scan` | Имя ИС/продукта (подгруппа под `…/itbigdata/`). Из него же берётся namespace и label `informationSystem`. |
| `template_type` | да | `python-fastapi` | Один из: `python-fastapi`, `python-flask`, `python-gunicorn`, `java`, `node`. |
| `deploy_stands` | да | `DEV` | `DEV` → только dev; `DEV + PREPROD`; `DEV + PREPROD + PROD`. Определяет, какие `<dc>-values.yaml` сгенерятся. |
| `pam_source` | если есть секреты | `LLM/cost_scan` | Путь в PAM **без** сегмента стенда (`dev/…` подставится сам): `<1 уровень>/<2 уровень>`. |
| `pg_enabled` / `pg_host` / `pg_db` | нет | `false` | Подключить PostgreSQL + хост/база. При `true` нужны PAM-секреты пароля/юзера. |
| `redis_enabled` / `redis_host` | нет | `false` | Подключить Redis. |
| `ch_enabled` / `ch_host` / `ch_db` | нет | `false` | Подключить ClickHouse. |
| `s3_enabled` / `s3_endpoint_url` / `s3_bucket` / `s3_prefix` | нет | `false` | Подключить S3. |
| `servicemonitor_enabled` | нет | `false` | Сбор кастомных метрик Prometheus с `/eapi/<app>/manage/prometheus`. Включай, только если приложение реально отдаёт метрики по этому пути. |
| `delete_password` | только delete | — | Пароль подтверждения удаления. Для `create` не нужен. |

> ℹ️ У каждого поля в форме есть подсказка (description) — читай её прямо в Run pipeline.
>
> ⚠️ Включил интеграцию (`*_enabled = true`) — **проверь, что соответствующий PAM-секрет существует** по пути `pam_source`. Иначе под не поднимется.

---

## 3. Что генератор сделал автоматически

После зелёного пайплайна:

1. **Два репозитория** (get-or-create, повторный запуск переиспользует):
   - код приложения: `middle/itbigdata/<target_group_name>/<project_name>`
   - конфигурация (Dockerfile, helm, config.yaml, Makefile): `middleconf/itbigdata/<target_group_name>/<project_name>`
2. **Регистрация продукта** в `nmf-job-dsl` (`middle/itbigdata/<product>.yaml`) через MR — по нему Jenkins-сид строит дерево джоб.
3. **Webhook** на middle-репо → `https://jenkins.middle.megafon.ru/cicd-lib-webhooker/gitlab` (push).
4. **Авто-деплой скелета в dev**: генератор создаёт ветку `develop`, ждёт появления джоб в Jenkins, затем коммитом+тегом триггерит сборку → скелет приложения уезжает на `vlg-t2-dc-s`.
5. **`develop` сделана дефолтной веткой** app-репо (при клоне сразу виден код, а не пустой `master`).

> ✅ То есть **после генератора в dev уже крутится рабочий скелет** (health отвечает на `/eapi/<app>/manage/health`). Дальше — наполняешь его своим кодом.

---

## 4. Шаг 2 — Разработка

```bash
git clone https://cicd-git.megafon.ru/middle/itbigdata/<target_group_name>/<project_name>.git
cd <project_name>          # окажешься на ветке develop с кодом шаблона
```

### Структура шаблона и обязательные правила

| Тип | Где код | Точка входа | Health (НЕ менять путь) |
|---|---|---|---|
| python-fastapi | `project/` (uv, `pyproject.toml`) | `uvicorn main:app` | роут под `/eapi/<app>/manage/health` |
| python-flask | `project/` (`requirements.txt`) | `gunicorn main:app` | Blueprint `url_prefix=/eapi/<app>` |
| python-gunicorn | `project/` + `gunicorn.conf.py` | `gunicorn -c gunicorn.conf.py main:app` | как flask |
| java | `src/…` (Spring Boot 2.7, **Java 11**) | `java -jar app.jar` | `server.servlet.context-path=/eapi/<app>` |
| node | `src/` (express) | `node src/index.js` | роутер под `/eapi/${APP_NAME}` |

**Жёсткие правила (иначе под не поднимется):**
- **Health всегда под `/eapi/<app>/manage/health`** — istio не срезает префикс, проба бьёт в полный путь.
- **Порт в коде — только из env** (`PORT` / `SERVER_PORT`). Плейсхолдер `{{SERVICE_PORT}}` работает **только** в `middleconf` (Dockerfile), в коде приложения он НЕ подставляется.
- Корень контейнера **read-only** — писать можно в `/tmp` (примонтирован tmpfs).

### Деплой изменений в dev

```bash
git add -A
git commit -m "feat: моя логика"
git push origin develop          # push в ветку ≠ master → сборка + деплой в dev
```

---

## 5. Деплой по стендам (детально)

> 🔑 **ГЛАВНОЕ ПРАВИЛО (из регламента Фабрики):**
> **Без свободного нового ТЭГА деплоя ни на какие кластеры не будет.**
> Перед выкаткой (особенно ветки, которую льёшь в master) создай новый тег вида `x.y.z` (semver) и **запушь его вместе с коммитом** (`git push --tags`). Версия берётся как `git describe --abbrev=0 --tags`.

### 5.1 DEV (Sandbox) — `vlg-t2-dc-s`

- **Триггер:** новый тег + коммит в **любую ветку, кроме `master`** (обычно `develop`).
  - либо коммит в `develop`, либо в любую другую не-master ветку.
- **Что уже сделано:** генератор выкатил скелет автоматически. Дальше каждый `git push origin develop` пересобирает и редеплоит.
- **Ресурсы:** 250m CPU / 256Mi RAM на продукт.
- **Версия артефакта:** dev → `<tag>-<source_branch>` (напр. `1.0.0-develop`).
- **Проверка:** см. раздел 7.

### 5.2 PREPROD (Lambda) — `vlg-t2-dc-l`

- **Предпосылка:** при запуске генератора `deploy_stands` должен включать **PREPROD** (иначе не будет `vlg-t2-dc-l-values.yaml`). Если выбирал только `DEV` — перезапусти генератор с `DEV + PREPROD` (репо переиспользуется) или добавь values-файл вручную.
- **Триггер:** **MR из ветки с тегом в `master`** (например `develop → master`). Деплой в лямбду идёт, если по открытому MR:
  - сделан коммит в ветку-источник MR, **или**
  - добавлен комментарий в MR.
- **Ресурсы:** 250m / 256Mi на продукт.
- **Версия:** test → `<tag>-rc`.

```bash
# из develop с уже созданным тегом
# создаём MR develop -> master (через UI GitLab или git push -o merge_request.create)
# затем коммит/коммент в MR запускает деплой в preprod
```

### 5.3 PROD (kb/dm) — `msk-p1-dm-gen` + `msk-p1-kb-gen`

- **Триггер:** **принятие (merge) MR в `master`**.
- **Версия:** prod → `<tag>` (без суффикса).
- **Доп. предпосылки для PROD (обязательны):**
  - **Infosec DFW** — открытие egress-портов с приложением infosec (`https://dfw.megafon.ru/list-infsys-rules`).
  - **HLD/LLD** — схемы, утверждённые ИБ.
  - **Ресурсы** под продукт согласованы (см. приложение — таблица CPU/RAM по ИС).
  - Регламенты: Приказ ITG №5/5-ITG-П11-001/25 и Приказ SCG №5/5-SCG-П08-004/25.
- **Security-сканы (PT AI / CodeScoring / AQUA) на prod НЕ отключаемы** — отчёты обязательны перед выкаткой релиза.
- **Релизные артефакты в prod не пересобираются** — копируются из rc с переименованием (консистентность версий).

> ⚠️ Деплой в prod на оба кластера (КБ и DM) — это два отдельных `<zone>-values.yaml` (`msk-p1-kb-gen-values.yaml`, `msk-p1-dm-gen-values.yaml`), которые генерятся при `deploy_stands = DEV + PREPROD + PROD`.

---

## 6. Ветвление (Git Flow) и версионирование (теги)

### 6.1 Модель ветвления (Git Flow)

На Фабрике используется **Git Flow** — долгоживущие ветки `master` и `develop` + короткие `feature/*`. **Стенд деплоя определяется типом git-события с веткой**, а не ручным выбором.

| Ветка / событие | Назначение | Стенд деплоя |
|---|---|---|
| **`master`** | прод, только релизы (защищённая) | PROD — при **merge** MR в master |
| **`develop`** | основная ветка разработки | DEV — при коммите (любой коммит в ≠ master) |
| **`feature/*`** | фича от `develop`, вливается обратно в `develop` через MR | DEV — коммит в ветку ≠ master тоже катит на dev |
| MR `develop → master` | подготовка релиза | PREPROD — при открытом MR в master (+ коммит/коммент в MR) |
| **`hotfix/*`** | срочная правка от `master` | по тем же правилам (MR в master → preprod/prod) |

**Рабочий цикл фичи:**
```bash
git checkout develop && git pull
git checkout -b feature/my-feature        # ветвимся от develop
# ... код ...
git commit -am "feat: ..." && git push origin feature/my-feature   # → деплой на DEV
# MR feature/my-feature -> develop, ревью, merge
# когда develop готов к релизу: MR develop -> master  → PREPROD, затем merge → PROD
```

> ℹ️ Не путать с **GitHub Flow** (только `main` + короткие feature → PR → main, без `develop`). У нас именно **Git Flow** (`master` + `develop` + `feature/*`), наложенный на деплой по событиям (как в GitLab Flow с environment-ветками).
>
> 🔑 **На каждый стенд деплой идёт только при наличии свободного нового тега** (см. ниже). Ветка определяет *куда*, тег — *что* версионируется.

### 6.2 Версионирование (теги)

- **Тег обязателен — без свободного нового тега деплоя не будет** ни на один стенд (правило ядра Фабрики).
- Формат — **semver** `MAJOR.MINOR.PATCH` (`0.0.x`, `0.y.x`, `x.y.z`, только числа):
  - `MAJOR` — несовместимые изменения; `MINOR` — новая обратно-совместимая функциональность; `PATCH` — фиксы.
- **Один тег = одна версия.** Перед выкаткой создавай **новый** тег (старый «занят»).
- **Тег вешается на коммит, который пойдёт в master** (на нём же основывается MR).
- **Пушить тег вместе с коммитом:** `git push --tags` (или галка *Push tags* в IDE) — по умолчанию теги в origin не уходят.
- Версия вычисляется по последнему тегу в source-ветке: `git describe --abbrev=0 --tags`.
- **Суффикс версии по событию** (формирует ядро автоматически):
  - DEV — `<tag>-<source_branch>` (напр. `1.0.1-develop`)
  - PREPROD (test) — `<tag>-rc`
  - PROD — `<tag>` (без суффикса)

```bash
git tag 1.0.1                      # новый свободный semver-тег
git push origin develop --tags     # коммит + тег → триггер деплоя
```

> ⚠️ Частая ошибка: запушить коммит **без** тега или с уже использованным тегом → деплой не стартует. Всегда новый тег + `--tags`.

---

## 7. Проверка деплоя

1. **Jenkins** — дерево джоб продукта:
   `https://jenkins.middle.megafon.ru/job/middle/job/itbigdata/job/<target_group_name>/job/<project_name>/`
   Внутри: `ci-job → docker-job → helm-job → cd-vlg-t2-dc-s` (для dev). Зелёные `#N` = успех.
2. **Rancher** (dev): namespace ИС → под сервиса в статусе Running.
   - DEV: `https://vlg-cicdt-rch.megafon.ru/dashboard/c/c-m-cdgvv8bg/explorer/projectsnamespaces`
   - PREPROD: `https://vlg-cicdt-rch.megafon.ru/dashboard/c/c-m-hc9mv792/explorer/projectsnamespaces`
   - PROD: `https://msk-cicd-rch.megafon.ru/dashboard/c/c-m-dhn4vz5g/…` (DM), `…/c-m-wwx9v5br/…` (КБ)
3. **Health-проба** — в логах пода должен отвечать `GET /eapi/<app>/manage/health → 200`.
4. **Логи/события** пода — при падении смотри Events (kyverno/ESO/probe).

---

## 8. Troubleshooting

### 8.0 Принцип траблшутинга — куда смотреть по слоям

Ошибка может быть на одном из трёх слоёв. Идём **сверху вниз**, пока не найдём первопричину:

```
GitLab pipeline  ──(клик по упавшей стадии)──►  Jenkins (лог job)  ──(если лог неинформативен)──►  Rancher (под/деплоймент в namespace)
   ЧТО упало                                       ПОЧЕМУ упала сборка/деплой              ПОЧЕМУ не стартует контейнер в k8s
```

> 🔐 **Авторизация и в Jenkins, и в Rancher — по короткой корпоративной УЗ** (логин вида `ivanov_ii`, доменный пароль). Если доступа нет — запросить у DevOps (`it-reporting-deployment-devops@megafon.ru`, заявки в Jira [DATA](https://jira.megafon.ru/browse/DATA)).

#### Слой 1. GitLab — пайплайн приложения (НЕ генератора)

После пуша в `develop` (или MR) в **middle-репо** твоего сервиса открой **CI/CD → Pipelines** → последний пайплайн.
- Видно цепочку стадий: `ci-job → docker-job → helm-job → cd-<zone>`. **Красная стадия = где упало.**
- Это «верхнеуровневый» статус: GitLab лишь показывает результат джоб Jenkins. Детали — внутри Jenkins.
- **Клик по упавшей стадии** → переход (по ссылке job) в Jenkins.

#### Слой 2. Jenkins — лог конкретной джобы

1. После клика откроется страница job в Jenkins → **авторизуйся короткой УЗ**.
2. Открой **последнюю сборку** (`#N` слева, обычно подсвечена красным) → **Console Output** (полный лог) либо **Pipeline Steps / Blue Ocean** для наглядного дерева шагов.
3. **Как искать ошибку в логе:**
   - Жми **End / Ctrl+F** и ищи (снизу вверх) ключевые слова: `ERROR`, `FAILED`, `Error:`, `Exception`, `Caused by`, `exit code`, `non-zero`, `denied`, `npm error`, `mvn … BUILD FAILURE`.
   - Смотри **последний** блок перед падением — обычно первопричина прямо над строкой `make: *** … Error 1` / `script returned exit code`.
   - По стадиям: ошибка в **ci/docker-job** → проблема сборки (код/зависимости/Dockerfile); в **helm-job** → проблема чарта/`values.yaml`; в **cd-job** → проблема деплоя в кластер (вот тут часто нужен Слой 3).
4. Полезное: в логе `cd-job` печатается namespace и kubectl-контекст — пригодится для Слоя 3.

#### Слой 3. Rancher — состояние пода/деплоймента (если лог Jenkins неинформативен)

Если `cd-job` упал/завис, а лог говорит лишь «deploy timeout» / «pod not ready» — иди смотреть **реальное состояние в кластере**.

1. Открой Rancher нужного стенда (ссылки — приложение 10.1):
   - DEV → `vlg-cicdt-rch.megafon.ru` (кластер `vlg-t2-dc-s`)
   - PREPROD → тот же Rancher, кластер `vlg-t2-dc-l`
   - PROD → `msk-cicd-rch.megafon.ru` (`msk-p1-dm-gen` / `msk-p1-kb-gen`)
2. **Авторизуйся короткой УЗ.**
3. Выбери **свой кластер** → слева **Workloads → Pods** (или **Deployments**) → сверху выбери **namespace своей ИС** (= `target_group_name`).
4. Найди под сервиса (`<project_name>-…`). Смотри:
   - **колонку статуса** (Running / CrashLoopBackOff / Pending / ContainerCreating / Terminating) — см. «Топ-10» ниже;
   - **вкладку Events** пода/деплоймента — там пишется первопричина (`exceeded quota`, `secret not found`, `probe failed`, `OOMKilled`, `FailedScheduling`);
   - **вкладку Logs** — `⋮` у пода → **View Logs** (если контейнеров два — выбери основной, а не `istio-proxy`);
   - при необходимости **⋮ → Execute Shell** (`kubectl exec`) для проверки изнутри.
5. То же из CLI, если есть kubeconfig:
   ```bash
   kubectl get pods -n <namespace>
   kubectl describe pod <pod> -n <namespace>     # блок Events внизу — главное
   kubectl logs <pod> -n <namespace> --previous  # лог упавшего контейнера
   ```

> 🧭 **Правило:** GitLab отвечает на «**что** упало», Jenkins — «**почему** не собралось/не задеплоилось», Rancher — «**почему контейнер не живёт** в k8s». Не застревай на верхнем слое: красная стадия в GitLab без чтения лога Jenkins (а часто и Rancher) причину не покажет.

### 8.1 Частые ошибки сборки/деплоя (специфика Фабрики)

| Симптом | Причина | Решение |
|---|---|---|
| `404` на `/eapi/<app>/manage/health`, под рестартует | health-роут не под префиксом `/eapi/<app>` | Все роуты под `/eapi/<app>` (istio префикс не срезает). В шаблонах генератора уже так. |
| `'{{SERVICE_PORT}}' is not a valid port number` | плейсхолдер порта в коде приложения (app-репо) | В коде порт брать из env (`PORT`); `{{SERVICE_PORT}}` допустим только в `middleconf/Dockerfile`. |
| `Read-only file system` (java/Tomcat → `/tmp/tomcat.*`) | `readOnlyRootFilesystem: true` | tmpfs на `/tmp` уже в `helm-base/values.yaml`. Если пишешь в другой путь — добавь volumeMount. |
| node build: `always-auth is not a valid npm option` | npm 9+ в build_image | registry-scoped `//host/:_auth` (в Makefile node уже исправлено). |
| Деплой не стартует после пуша | нет нового свободного тега / push был branch-create | Создай новый тег и запушь вместе с коммитом (`git push --tags`); триггерит branch-update. |
| `400 PLEASE CHECK … NAMESPACE LABELS` | label `informationSystem` не из ФНС | Указать корректное англ. название ИС из `cmdb.megafon.ru` → ФНС. |
| `admission webhook validate.kyverno … denied` | нет корректного `securityContext` в кастомном deployment/job | Добавить `securityContext` (runAsNonRoot/readOnlyRootFilesystem/drop ALL и т.д.). |
| `ScanError` в helm-job | битый YAML (лишний пробел/таб) в `values.yaml` | Открыть в редакторе со спецсимволами у строки из ошибки. |
| Приложение не успевает стартовать за таймаут | долгая инициализация | `generic.deployTimeout: "7m"` в values.yaml. |
| ESO: нет `<app>-secrets-from-pam` | PAM не отдаёт секрет | Проверить путь/доступ SAPM-аккаунта (`kubectl describe externalsecret …`). |

### 8.2 Топ-10 частых ошибок деплоя в Kubernetes

> Базовая диагностика по любому поду: `kubectl describe pod <pod> -n <ns>` (смотри блок **Events** и **Last State**) и `kubectl logs <pod> -n <ns> [--previous]`. В Rancher то же — вкладка пода → Events / Logs.

| # | Статус/ошибка | Что значит и частая причина | Диагностика | Решение |
|---|---|---|---|---|
| 1 | **CrashLoopBackOff** | Контейнер стартует и сразу падает, k8s рестартует по нарастающему backoff. Причина: исключение на старте, неверный конфиг/env, отсутствует зависимость. | `kubectl logs <pod> --previous` | Починить причину падения в коде/конфиге. Проверить env и подключённые секреты. |
| 2 | **ImagePullBackOff / ErrImagePull** | Не скачивается образ. Причина: тег образа не существует, нет/неверный `imagePullSecret`, registry недоступен, неверный путь образа. | `describe pod` → Events (`Failed to pull image …`) | Проверить тег/путь образа и `imagePullSecrets` (`mf-artifactory-registry`); убедиться, что docker-job собрал и запушил образ. |
| 3 | **OOMKilled** | Контейнер убит за превышение **memory limit**. На dev лимит всего **256Mi** — легко словить. | `describe pod` → Last State: `OOMKilled` | Поднять `resources.limits.memory` (в рамках квоты) или оптимизировать память приложения. |
| 4 | **forbidden: exceeded quota** (FailedCreate) | Исчерпана **ResourceQuota** namespace ИС — deployment/replicaset не может создать под. На Фабрике dev/preprod квота = 250m/256Mi на продукт. | `kubectl describe quota -n <ns>`; события ReplicaSet `FailedCreate` | Уменьшить `requests/limits` сервиса **или** запросить увеличение namespace-квоты у DevOps. |
| 5 | **Pending / FailedScheduling** (`Insufficient cpu/memory`) | Под не шедулится: на нодах нет ресурсов под `requests`, либо node-selector/taints не совпали. | `describe pod` → Events (`0/N nodes available`) | Снизить `requests`, проверить affinity/priorityClass; при нехватке мощностей — к DevOps. |
| 6 | **CreateContainerConfigError** | Под не создаётся: ссылается на **отсутствующий Secret/ConfigMap** (частый кейс — `<app>-secrets-from-pam` ещё не создан ESO, т.к. интеграция включена, а PAM-секрет не заведён). | `describe pod` → Events (`secret … not found`) | Завести PAM-секрет по `pam_source`, либо отключить интеграцию (`*_enabled=false`), если она не нужна. |
| 7 | **Readiness/Liveness/Startup probe failed** | Проба не проходит (404 / timeout / connection refused) → под не Ready или рестартует. На Фабрике топ-причина: health не под `/eapi/<app>` или приложение слушает не тот порт. | `describe pod` → Events (`Readiness probe failed: HTTP 404`); `logs` | Health под `/eapi/<app>/manage/health`; порт из env; при долгом старте — `startupProbe`/`deployTimeout`. |
| 8 | **helm/App «завис»: another operation (install/upgrade/rollback) is in progress** | Деплой пишет, что **процесс деплоя уже запущен** — релиз застрял в `pending-*` после прерванного/зависшего пайплайна (зомби-релиз). Бывает часто. НЕ прерывать стадию CD без нужды! | `helm history <release> -n <ns>` (статус `pending-upgrade` = зомби) | **Вариант А (быстрый, проверенный):** удалить зависшее приложение (App/helm-релиз) — в Rancher **Apps → Installed Apps** найти релиз сервиса → `⋮` → **Delete**, затем перезапустить деплой (передеплой из CI). **Вариант Б:** `helm rollback <release> <revision> -n <ns>` на последнюю успешную ревизию. |
| 9 | **Pod stuck Terminating / ContainerCreating** | Под «висит»: Terminating (финализаторы, зависший volume/нода) или ContainerCreating (не монтируется volume, тянется образ, sidecar istio не поднялся). | `describe pod` → Events; `kubectl get events -n <ns> --sort-by=.lastTimestamp` | Дождаться; при зависшем volume — `FailedMount` смотреть; крайняя мера — `kubectl delete pod --grace-period=0 --force`. |
| 10 | **admission webhook denied** (kyverno / quota / labels) | Политика кластера блокирует создание ресурса: некорректный `securityContext`, неверный label `informationSystem`, нарушение quota-политики. | Ошибка в выводе `helm`/`kubectl` (`validate.kyverno.svc … denied`) | Добавить требуемый `securityContext`; указать корректный label ИС из ФНС; см. строки kyverno/labels выше. |

> ℹ️ **Истио-нюанс:** если приложение в namespace с istio-инъекцией, под содержит ещё и sidecar `istio-proxy`. Пока sidecar не готов — основной контейнер может «висеть» в `Not Ready`. Смотри состояние **обоих** контейнеров: `kubectl get pod <pod> -o wide` и логи `kubectl logs <pod> -c istio-proxy`.

---

## 9. Удаление сервиса (`action=delete`)

1. Run pipeline генератора: `action=delete`, `project_name` + `target_group_name` = удаляемая цель, `delete_password` = пароль подтверждения.
2. Удаляются: **оба репо** (`middle` + `middleconf`) и строка продукта в `nmf-job-dsl` (через MR). **Группа/ИС не трогается.**
3. Требуется роль **Owner** в GitLab (Maintainer → 403).
4. Папки джоб в Jenkins сид сносит асинхронно (несколько минут) — это нормально.

---

## 10. Приложения

### 10.1 Стенды и ресурсы

| Стенд | Кластер | Ресурсы/продукт | Rancher |
|---|---|---|---|
| DEV (Sandbox) | `vlg-t2-dc-s` | 250m / 256Mi | `vlg-cicdt-rch.megafon.ru/.../c-m-cdgvv8bg` |
| PREPROD (Lambda) | `vlg-t2-dc-l` | 250m / 256Mi | `vlg-cicdt-rch.megafon.ru/.../c-m-hc9mv792` |
| PROD | `msk-p1-dm-gen` + `msk-p1-kb-gen` | по таблице ИС | `msk-cicd-rch.megafon.ru/.../c-m-dhn4vz5g` (DM), `…/c-m-wwx9v5br` (КБ) |

### 10.2 PAM — пути секретов (dev)

`/MegaFon/Common/Data-Analytics/<stand>/<pam_source>/` — `<stand>` (`dev`/`preprod`/`prod`) подставляется генератором. Примеры (dev):
- `…/dev/LLM/bot_forge/`
- `…/dev/LLM/call_analizer/`
- `…/dev/LLM/cost_scan/`
- `…/dev/LLM/ocr_abd/`

### 10.3 Продукты / ИС-коды и prod-ресурсы

| Продукт (target_group) | ИС-код | PROD CPU/RAM (на кластер) |
|---|---|---|
| llm-botforge | IS00005338 | 8 ядер / 16 ГБ |
| costscan | IS00005340 | 2 / 4 |
| ai-call-analizer | IS00005339 | 8 / 16 |
| ocr-abd | IS00005337 | 4 / 8 |

### 10.4 Полезные ссылки

- Документация ядра CI/CD (MfactoryCI) — события, теги, helm, config.yaml.
- `nmf-job-dsl`: `https://cicd-git.megafon.ru/libs/cicd/nmf/nmf-job-dsl/-/tree/master/middle/itbigdata`
- DFW (egress-правила): `https://dfw.megafon.ru/list-infsys-rules`
- Webhook сборки: `https://jenkins.middle.megafon.ru/cicd-lib-webhooker/gitlab`
- Регламенты: Приказ ITG №5/5-ITG-П11-001/25 (06.11.2025), Приказ SCG №5/5-SCG-П08-004/25 (12.08.2025).
