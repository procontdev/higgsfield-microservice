from fastapi import FastAPI

from app.config import settings
from app.routes.video import router as video_router

app = FastAPI(
    title="Higgsfield Microservice",
    version="0.2.2",
    description="Microservicio Python para integración de generación de video con Higgsfield",
)


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "higgsfield-microservice",
        "env": settings.app_env,
        "activeProvider": settings.active_video_provider,
        "executionEnabled": settings.higgsfield_execution_enabled,
        "testMode": settings.higgsfield_test_mode,
        "allowedJobId": settings.higgsfield_allowed_job_id or None,
        "maxDurationSeconds": settings.higgsfield_max_duration_seconds,
        "modelConfigured": settings.model_configured,
        "modelId": settings.higgsfield_model_id or None,
        "modelLabel": settings.model_display_name,
        "credentialsConfigured": settings.credentials_configured,
    }


app.include_router(video_router)