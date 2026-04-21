FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/maven:3-eclipse-temurin-21-alpine AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/ibm-semeru-runtimes:open-21-jre-jammy
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
