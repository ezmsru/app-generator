from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "{{PROJECT_NAME}}"
    DEBUG: bool = False

    # PostgreSQL
    PG_HOST: str = ""
    PG_PORT: int = 5432
    PG_DB: str = ""
    PG_USER: str = ""
    PG_PASSWORD: str = ""

    # Redis
    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379

    # ClickHouse
    CH_HOST: str = ""
    CH_PORT: int = 8123
    CH_DB: str = ""
    CH_USER: str = ""
    CH_PASSWORD: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
