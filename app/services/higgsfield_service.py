from __future__ import annotations

import base64
import os
import threading
import uuid
from typing import Any, Dict

from app.config import settings
from app.models import GenerateVideoRequest
from app.services.task_store import task_store


class HiggsfieldService:
    def __init__(self) -> None:
        self.provider_name = "higgsfield"

    def _build_initial_task(self, payload: GenerateVideoRequest) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())
        return {
            "id": task_id,
            "jobId": payload.jobId,
            "provider": self.provider_name,
            "status": "queued",
            "resultUrl": None,
            "videoFileName": None,
            "videoMimeType": None,
            "error": None,
            "requestId": None,
        }

    def create_video_task(self, payload: GenerateVideoRequest) -> Dict[str, Any]:
        if settings.active_video_provider != "higgsfield":
            raise ValueError(
                f"ACTIVE_VIDEO_PROVIDER actual es '{settings.active_video_provider}', no 'higgsfield'."
            )

        task = self._build_initial_task(payload)
        task_store.create_task(task)

        if not settings.higgsfield_execution_enabled:
            task_store.update_task(
                task["id"],
                {
                    "status": "failed",
                    "error": (
                        "HIGGSFIELD_EXECUTION_ENABLED=false. "
                        "La ejecución real está deshabilitada para evitar consumo accidental de créditos."
                    ),
                },
            )
            return task_store.get_task(task["id"])

        if not settings.higgsfield_model_id:
            task_store.update_task(
                task["id"],
                {
                    "status": "failed",
                    "error": "HIGGSFIELD_MODEL_ID no está configurado.",
                },
            )
            return task_store.get_task(task["id"])

        worker = threading.Thread(
            target=self._process_task_safe,
            args=(task["id"], payload),
            daemon=True,
        )
        worker.start()

        return task_store.get_task(task["id"])

    def _process_task_safe(self, task_id: str, payload: GenerateVideoRequest) -> None:
        try:
            self._process_task(task_id, payload)
        except Exception as exc:
            task_store.update_task(
                task_id,
                {
                    "status": "failed",
                    "error": str(exc),
                },
            )

    def _process_task(self, task_id: str, payload: GenerateVideoRequest) -> None:
        task_store.update_task(task_id, {"status": "running"})

        try:
            image_bytes = base64.b64decode(payload.imageBase64, validate=True)
        except Exception:
            raise ValueError("imageBase64 no tiene un base64 válido.")

        if not image_bytes:
            raise ValueError("imageBase64 está vacío después de decodificar.")

        temp_dir = os.path.join(os.getcwd(), "tmp")
        os.makedirs(temp_dir, exist_ok=True)

        temp_input_path = os.path.join(temp_dir, f"{task_id}-{payload.fileName}")
        with open(temp_input_path, "wb") as f:
            f.write(image_bytes)

        raise RuntimeError(
            "Modo ejecución real habilitado, pero la llamada efectiva al SDK aún no fue implementada."
        )

    def get_task(self, task_id: str) -> Dict[str, Any] | None:
        return task_store.get_task(task_id)


higgsfield_service = HiggsfieldService()