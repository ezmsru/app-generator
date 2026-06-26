.PHONY: unitTests sonarQube buildApp

# LANG_PATH/USER/PASSWORD прокидываются ядром MfactoryCI на стороне Jenkins.
NPM_REGISTRY := https://unixrepo.megafon.ru/artifactory/api/npm/mfactory-npm

# Тесты и статанализ на старте не нужны — no-op (как и в python/java-шаблонах).
unitTests:
	@echo "тесты отключены"

sonarQube:
	@echo "sonar отключён"

# buildApp ставит зависимости и складывает ВСЁ для рантайма в srcDirectory (app):
# src/ + node_modules/ + package.json. Dockerfile (runtime) берёт это из ./app.
buildApp:
	cd ${LANG_PATH} && \
	  npm config set registry ${NPM_REGISTRY} && \
	  npm config set always-auth true && \
	  npm config set _auth "$$(printf '%s:%s' '${USER}' '${PASSWORD}' | base64 -w 0)" && \
	  npm install --omit=dev
	mkdir -p ${LANG_PATH}/app
	cp -r ${LANG_PATH}/src ${LANG_PATH}/node_modules ${LANG_PATH}/package.json ${LANG_PATH}/app/
