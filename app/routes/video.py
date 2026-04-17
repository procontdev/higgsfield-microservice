from fastapi import APIRouter, HTTPException

from app.models import GenerateVideoRequest, GenerateVideoResponse, TaskResponse
from app.services.higgsfield_service import higgsfield_service

router = APIRouter(prefix="/video", tags=["video"])


@router.post("/generate-video", response_model=GenerateVideoResponse)
def generate_video(payload: GenerateVideoRequest):
    if payload.provider.strip().lower() != "higgsfield":
        raise HTTPException(
            status_code=400,
            detail="Este microservicio solo acepta provider='higgsfield'.",
        )

    try:
        task = higgsfield_service.create_video_task(payload)
        message = "Tarea registrada correctamente."

        if task["status"] == "failed" and task.get("error"):
            message = task["error"]

        return GenerateVideoResponse(
            id=task["id"],
            jobId=task["jobId"],
            provider=task["provider"],
            status=task["status"],
            message=message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    task = higgsfield_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task no encontrada.")

    return TaskResponse(
        id=task["id"],
        jobId=task["jobId"],
        provider=task["provider"],
        status=task["status"],
        resultUrl=task.get("resultUrl"),
        videoFileName=task.get("videoFileName"),
        videoMimeType=task.get("videoMimeType"),
        error=task.get("error"),
    )