module.exports = {
  APP_NAME: process.env.APP_NAME || "{{PROJECT_NAME}}",
  PORT: parseInt(process.env.PORT || "3000", 10),

  // PostgreSQL
  PG_HOST: process.env.PG_HOST || "",
  PG_PORT: parseInt(process.env.PG_PORT || "5432", 10),
  PG_DB: process.env.PG_DB || "",
  PG_USER: process.env.PG_USER || "",
  PG_PASSWORD: process.env.PG_PASSWORD || "",

  // Redis
  REDIS_HOST: process.env.REDIS_HOST || "",
  REDIS_PORT: parseInt(process.env.REDIS_PORT || "6379", 10),

  // ClickHouse
  CH_HOST: process.env.CH_HOST || "",
  CH_PORT: parseInt(process.env.CH_PORT || "8123", 10),
  CH_DB: process.env.CH_DB || "",
  CH_USER: process.env.CH_USER || "",
  CH_PASSWORD: process.env.CH_PASSWORD || "",
};
