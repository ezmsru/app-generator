from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)


@bp.route("/")
def root():
    return jsonify({"message": "Hello from {{PROJECT_NAME}}"})


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})
