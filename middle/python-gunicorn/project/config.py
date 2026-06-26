import os


class Config:
    APP_NAME = os.getenv("APP_NAME", "{{PROJECT_NAME}}")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    PG_HOST = os.getenv("PG_HOST", "")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_DB = os.getenv("PG_DB", "")
    PG_USER = os.getenv("PG_USER", "")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "")

    REDIS_HOST = os.getenv("REDIS_HOST", "")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

    CH_HOST = os.getenv("CH_HOST", "")
    CH_PORT = int(os.getenv("CH_PORT", "8123"))
    CH_DB = os.getenv("CH_DB", "")
    CH_USER = os.getenv("CH_USER", "")
    CH_PASSWORD = os.getenv("CH_PASSWORD", "")
