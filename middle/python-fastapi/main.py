from fastapi import FastAPI
from config import settings
from routes import router

app = FastAPI(title=settings.APP_NAME, version="1.0.0")
app.include_router(router)


@app.get("/health")
@app.get("/manage/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
