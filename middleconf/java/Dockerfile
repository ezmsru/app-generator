# RUNTIME-ONLY по модели MfactoryCI: jar уже собран build_image'ом через
# make-таргет buildApp (package→copy) и лежит в srcDirectory app. Dockerfile
# его НЕ компилирует, только формирует лёгкий рантайм-образ.
FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/ibm-semeru-runtimes:open-21-jre-jammy

WORKDIR /data/app

# srcDirectory app наполняется make-таргетом buildApp: там лежит app.jar.
COPY ./app/*.jar /data/app/app.jar

RUN chown -R 11200 /data/app
USER 11200

EXPOSE {{SERVICE_PORT}}
# Прямой exec-вход (java = PID 1, корректная обработка SIGTERM) — best practice доки.
# Порт и префикс /eapi/<app> — из подставляемых плейсхолдеров (middleconf):
# server.servlet.context-path сдвигает все роуты (вкл. /manage/health) под /eapi/<app>.
ENTRYPOINT ["java", "-jar", "/data/app/app.jar"]
CMD ["--server.port={{SERVICE_PORT}}", "--server.servlet.context-path=/eapi/{{PROJECT_NAME}}"]
