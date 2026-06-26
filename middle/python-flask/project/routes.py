import os

from flask import Blueprint, jsonify

# Истио/гейтвей НЕ срезает префикс — под получает полный путь /eapi/<app>/...,
# поэтому все роуты (вкл. health-пробу) объявляем под этим префиксом.
# APP_NAME приходит из env (helm) и совпадает с helpers.app.name в пробах.
APP_NAME = os.getenv("APP_NAME", "{{PROJECT_NAME}}")
bp = Blueprint("main", __name__, url_prefix=f"/eapi/{APP_NAME}")


@bp.route("/")
def root():
    return jsonify({"message": "Hello from {{PROJECT_NAME}}"})


@bp.route("/manage/health")
def health():
    return jsonify({"status": "ok", "app": APP_NAME})
