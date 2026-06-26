# RUNTIME-ONLY по модели MfactoryCI: зависимости (npm install) ставит build_image
# через make-таргет buildApp, который кладёт src + node_modules + package.json в
# srcDirectory app. Dockerfile их НЕ устанавливает, только формирует рантайм-образ.
FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/node:22-alpine

WORKDIR /data/app

# srcDirectory app наполняется make-таргетом buildApp: src/ + node_modules/ + package.json.
COPY ./app /data/app
COPY ${WORKSPACE}/cicd-conf/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod a+x /usr/local/bin/entrypoint.sh && chown -R 11200 /data/app
USER 11200

# PORT читает приложение (src/config.js); /eapi/<app>-префикс роутов — в src/index.js.
ENV PORT={{SERVICE_PORT}}
EXPOSE {{SERVICE_PORT}}
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["node", "src/index.js"]
