const express = require("express");
const config = require("./config");

const app = express();
app.use(express.json());

// Истио/гейтвей НЕ срезает префикс — под получает полный путь /eapi/<app>/...,
// поэтому все роуты (вкл. health-пробу) вешаем под этим префиксом.
// APP_NAME приходит из env (helm) и совпадает с helpers.app.name в пробах.
const router = express.Router();

router.get("/", (req, res) => {
  res.json({ message: `Hello from ${config.APP_NAME}` });
});

router.get(["/health", "/manage/health"], (req, res) => {
  res.json({ status: "ok", app: config.APP_NAME });
});

app.use(`/eapi/${config.APP_NAME}`, router);

app.listen(config.PORT, () => {
  console.log(`${config.APP_NAME} listening on port ${config.PORT}`);
});
