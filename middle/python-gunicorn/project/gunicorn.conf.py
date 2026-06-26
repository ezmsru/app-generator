# gunicorn.conf.py лежит в project/ → buildApp кладёт его плоско в /data/app,
# поэтому Dockerfile CMD `gunicorn -c gunicorn.conf.py main:app` его находит.
bind = "0.0.0.0:{{SERVICE_PORT}}"
workers = 4
worker_class = "sync"
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
