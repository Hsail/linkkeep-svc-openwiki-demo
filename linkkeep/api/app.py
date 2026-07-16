"""FastAPI 应用装配入口：`uvicorn linkkeep.api.app:app` 启动。"""
from fastapi import FastAPI

from .routes import router

app = FastAPI(title="linkkeep-svc", version="0.2.0", description="极简书签管理服务的 REST API 层")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
