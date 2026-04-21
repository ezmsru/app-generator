const express = require("express");
const config = require("./config");

const app = express();
app.use(express.json());

app.get("/", (req, res) => {
  res.json({ message: `Hello from ${config.APP_NAME}` });
});

app.get("/health", (req, res) => {
  res.json({ status: "ok", app: config.APP_NAME });
});

app.listen(config.PORT, () => {
  console.log(`${config.APP_NAME} listening on port ${config.PORT}`);
});
