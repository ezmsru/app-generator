FROM mf-ubi-target-docker-local.unixrepo.megafon.ru/node:22-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

EXPOSE 3000
CMD ["node", "src/index.js"]
