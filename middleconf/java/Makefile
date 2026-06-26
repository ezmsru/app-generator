.PHONY: preCheck unitTests sonarQube package copy buildApp

# LANG_PATH/USER/PASSWORD прокидываются ядром MfactoryCI на стороне Jenkins.
# settings.xml с maven-репозиториями и кредами лежит в скачанном buildpack.
SETTINGS := ${LANG_PATH}/product/buildpack/settings.xml

preCheck:
	mvn --version

# Тесты и статанализ на старте не нужны — no-op (как и в python-шаблонах).
unitTests:
	@echo "тесты отключены"

sonarQube:
	@echo "sonar отключён"

# package компилирует jar в стандартную для java директорию ${LANG_PATH}/target.
package: preCheck
	mvn clean package -DskipTests \
	  -Drepo.username=${USER} -Drepo.password=${PASSWORD} \
	  --settings ${SETTINGS} --batch-mode \
	  -Dorg.slf4j.simpleLogger.log.org.apache.maven.cli.transfer.Slf4jMavenTransferListener=warn

# copy кладёт собранный jar в srcDirectory (app) — оттуда его берёт runtime Dockerfile.
copy:
	mkdir -p ${LANG_PATH}/app
	cp ${LANG_PATH}/target/*.jar ${LANG_PATH}/app/

buildApp: package copy
