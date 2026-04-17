from __future__ import annotations

import base64
import os
import threading
import time
import uuid
from typing import Any, Dict, Optional

from app.config import settings
from app.models import GenerateVideoRequest
from app.services.task_store import task_store

try:
    import higgsfield_client
except ImportError:  # pragma: no cover
    higgsfield_client = None


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
            "debug": {
                "modelId": settings.higgsfield_model_id or None,
                "executionEnabled": settings.higgsfield_execution_enabled,
            },
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

        if not settings.credentials_configured:
            task_store.update_task(
                task["id"],
                {
                    "status": "failed",
                    "error": "Faltan credenciales de Higgsfield en variables de entorno.",
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

        image_bytes = self._decode_base64_image(payload.imageBase64)

        temp_input_path = self._write_temp_input_file(task_id, payload.fileName, image_bytes)

        # Etapa preparada:
        # 1) upload del asset
        # 2) submit del request
        # 3) polling de estado
        #
        # Aún no activamos el submit real al modelo hasta confirmar
        # el model_id exacto y el shape de arguments.
        uploaded_asset = self._prepare_upload_stub(temp_input_path)
        request_payload = self._build_submit_arguments_stub(payload, uploaded_asset)

        raise RuntimeError(
            "SDK preparado. Falta implementar submit real y polling final una vez confirmado "
            "HIGGSFIELD_MODEL_ID y argumentos exactos del modelo."
        )

    def _decode_base64_image(self, image_base64: str) -> bytes:
        try:
            image_bytes = base64.b64decode(image_base64, validate=True)
        except Exception as exc:
            raise ValueError("imageBase64 no tiene un base64 válido.") from exc

        if not image_bytes:
            raise ValueError("imageBase64 está vacío después de decodificar.")

        return image_bytes

    def _write_temp_input_file(self, task_id: str, file_name: str, image_bytes: bytes) -> str:
        temp_dir = os.path.join(os.getcwd(), "tmp")
        os.makedirs(temp_dir, exist_ok=True)

        temp_input_path = os.path.join(temp_dir, f"{task_id}-{file_name}")
        with open(temp_input_path, "wb") as f:
            f.write(image_bytes)

        return temp_input_path

    def _prepare_upload_stub(self, file_path: str) -> Dict[str, Any]:
        return {
            "localPath": file_path,
            "uploadedUrl": None,
            "uploadedAssetId": None,
        }

    def _build_submit_arguments_stub(
        self,
        payload: GenerateVideoRequest,
        uploaded_asset: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "prompt": payload.prompt,
            "durationSeconds": payload.durationSeconds,
            "inputImage": uploaded_asset.get("uploadedUrl"),
            "fileName": payload.fileName,
            "mimeType": payload.mimeType,
        }

    def _build_hf_env(self) -> None:
        if settings.hf_key:
            os.environ["HF_KEY"] = settings.hf_key
        elif settings.higgsfield_api_key and settings.higgsfield_api_secret:
            os.environ["HF_API_KEY"] = settings.higgsfield_api_key
            os.environ["HF_API_SECRET"] = settings.higgsfield_api_secret
        else:
            raise RuntimeError("No hay credenciales válidas de Higgsfield configuradas.")

    def _upload_asset_real(self, file_path: str) -> Dict[str, Any]:
        if higgsfield_client is None:
            raise RuntimeError("higgsfield-client no está instalado en el entorno.")

        self._build_hf_env()

        result = higgsfield_client.upload_file(file_path)
        return result

    def _submit_job_real(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if higgsfield_client is None:
            raise RuntimeError("higgsfield-client no está instalado en el entorno.")

        self._build_hf_env()

        result = higgsfield_client.submit(
            settings.higgsfield_model_id,
            arguments=arguments,
        )
        return result

    def _poll_job_real(
        self,
        request_id: str,
        timeout_seconds: int = 180,
        poll_interval_seconds: int = 5,
    ) -> Dict[str, Any]:
        started_at = time.time()

        while True:
            if time.time() - started_at > timeout_seconds:
                raise TimeoutError("La tarea de Higgsfield excedió el tiempo máximo de espera.")

            status_result = self._get_request_status_real(request_id)
            normalized = self._normalize_provider_status(status_result)

            if normalized in {"succeeded", "failed"}:
                return status_result

            time.sleep(poll_interval_seconds)

    def _get_request_status_real(self, request_id: str) -> Dict[str, Any]:
        raise RuntimeError(
            "Pendiente implementar consulta de estado real del request en Higgsfield."
        )

    def _normalize_provider_status(self, provider_response: Dict[str, Any]) -> str:
        raw_status = str(provider_response.get("status", "")).strip().lower()

        mapping = {
            "queued": "queued",
            "pending": "queued",
            "running": "running",
            "processing": "running",
            "in_progress": "running",
            "completed": "succeeded",
            "success": "succeeded",
            "succeeded": "succeeded",
            "failed": "failed",
            "error": "failed",
            "cancelled": "failed",
            "canceled": "failed",
        }

        return mapping.get(raw_status, "running")

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return task_store.get_task(task_id)


higgsfield_service = HiggsfieldService()