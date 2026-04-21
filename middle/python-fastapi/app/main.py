from fastapi import FastAPI
from app.config import settings
from app.routes import router

app = FastAPI(title=settings.APP_NAME, version="1.0.0")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
