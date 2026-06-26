from fastapi import APIRouter, FastAPI

from config import settings
from routes import router

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# Истио/гейтвей НЕ срезает префикс — под получает полный путь /eapi/<app>/...,
# поэтому все роуты (вкл. health/probes) объявляем под этим префиксом.
# APP_NAME приходит из env (helm) и совпадает с helpers.app.name в пробах.
PREFIX = f"/eapi/{settings.APP_NAME}"

manage = APIRouter(prefix=f"{PREFIX}/manage", tags=["manage"])


@manage.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(manage)
app.include_router(router, prefix=PREFIX)
