from fastapi import FastAPI

from app.config import settings
from app.routes.video import router as video_router

app = FastAPI(
    title="Higgsfield Microservice",
    version="0.1.0",
    description="Microservicio Python para integración de generación de video con Higgsfield",
)


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "higgsfield-microservice",
        "env": settings.app_env,
        "activeProvider": settings.active_video_provider,
    }


app.include_router(video_router)