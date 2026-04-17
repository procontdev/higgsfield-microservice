from typing import Literal, Optional
from pydantic import BaseModel, Field


NormalizedTaskStatus = Literal["queued", "running", "succeeded", "failed"]


class GenerateVideoRequest(BaseModel):
    jobId: str = Field(..., min_length=1)
    fileName: str = Field(..., min_length=1)
    imageBase64: str = Field(..., min_length=1)
    mimeType: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    durationSeconds: int = Field(default=4, ge=1, le=30)
    provider: str = Field(default="higgsfield")


class GenerateVideoResponse(BaseModel):
    id: str
    jobId: str
    provider: str
    status: NormalizedTaskStatus
    message: str


class TaskResponse(BaseModel):
    id: str
    jobId: str
    provider: str
    status: NormalizedTaskStatus
    resultUrl: Optional[str] = None
    videoFileName: Optional[str] = None
    videoMimeType: Optional[str] = None
    error: Optional[str] = None