import os

# gunicorn.conf.py лежит в project/ → buildApp кладёт его плоско в /data/app,
# поэтому Dockerfile CMD `gunicorn -c gunicorn.conf.py main:app` его находит.
# Порт берём из env PORT (его задаёт Dockerfile middleconf: ENV PORT={{SERVICE_PORT}}).
# В app-репо {{SERVICE_PORT}} НЕ подставляется (fill-template меняет только PROJECT_NAME).
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
workers = 4
worker_class = "sync"
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
