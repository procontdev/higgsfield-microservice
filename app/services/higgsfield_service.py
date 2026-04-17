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
                "modelLabel": settings.model_display_name,
                "executionEnabled": settings.higgsfield_execution_enabled,
                "testMode": settings.higgsfield_test_mode,
                "allowedJobId": settings.higgsfield_allowed_job_id or None,
                "maxDurationSeconds": settings.higgsfield_max_duration_seconds,
            },
        }

    def create_video_task(self, payload: GenerateVideoRequest) -> Dict[str, Any]:
        if settings.active_video_provider != "higgsfield":
            raise ValueError(
                f"ACTIVE_VIDEO_PROVIDER actual es '{settings.active_video_provider}', no 'higgsfield'."
            )

        self._validate_controlled_test_rules(payload)

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

    def _validate_controlled_test_rules(self, payload: GenerateVideoRequest) -> None:
        if not settings.higgsfield_test_mode:
            return

        if not settings.higgsfield_allowed_job_id:
            raise ValueError(
                "HIGGSFIELD_TEST_MODE=true pero HIGGSFIELD_ALLOWED_JOB_ID no está configurado."
            )

        if payload.jobId != settings.higgsfield_allowed_job_id:
            raise ValueError(
                f"Modo prueba controlada activo. Solo se permite jobId='{settings.higgsfield_allowed_job_id}'."
            )

        if payload.durationSeconds > settings.higgsfield_max_duration_seconds:
            raise ValueError(
                "durationSeconds excede el máximo permitido para prueba controlada: "
                f"{settings.higgsfield_max_duration_seconds}."
            )

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

        uploaded_url = self._upload_asset_real(temp_input_path)
        arguments = self._build_submit_arguments(payload, uploaded_url)

        current_task = task_store.get_task(task_id) or {}
        current_debug = current_task.get("debug", {})

        task_store.update_task(
            task_id,
            {
                "debug": {
                    **current_debug,
                    "submitArgumentsPreview": arguments,
                }
            },
        )

        request_controller = self._submit_job_real(arguments)
        request_id = self._extract_request_id(request_controller)

        task_store.update_task(
            task_id,
            {
                "requestId": request_id,
                "status": "running",
            },
        )

        final_status = self._poll_job_real(request_id=request_id)

        normalized_status = self._normalize_provider_status(final_status)
        if normalized_status == "failed":
            task_store.update_task(
                task_id,
                {
                    "status": "failed",
                    "error": self._extract_error_message(final_status),
                },
            )
            return

        result = self._get_result_real(request_id=request_id)
        result_url = self._extract_result_url(result)

        if not result_url:
            task_store.update_task(
                task_id,
                {
                    "status": "failed",
                    "error": "No se pudo extraer resultUrl desde la respuesta final del proveedor.",
                },
            )
            return

        task_store.update_task(
            task_id,
            {
                "status": "succeeded",
                "resultUrl": result_url,
                "videoFileName": self._build_video_file_name(payload.fileName),
                "videoMimeType": "video/mp4",
                "error": None,
            },
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

    def _build_hf_env(self) -> None:
        if settings.hf_key:
            os.environ["HF_KEY"] = settings.hf_key
            return

        if settings.higgsfield_api_key and settings.higgsfield_api_secret:
            os.environ["HF_API_KEY"] = settings.higgsfield_api_key
            os.environ["HF_API_SECRET"] = settings.higgsfield_api_secret
            return

        raise RuntimeError("No hay credenciales válidas de Higgsfield configuradas.")

    def _upload_asset_real(self, file_path: str) -> str:
        if higgsfield_client is None:
            raise RuntimeError("higgsfield-client no está instalado en el entorno.")

        self._build_hf_env()

        result = higgsfield_client.upload_file(file_path)
        if not result:
            raise RuntimeError("upload_file no devolvió una URL válida.")

        return str(result)

    def _build_submit_arguments(self, payload: GenerateVideoRequest, uploaded_url: str) -> Dict[str, Any]:
        model_id = (settings.higgsfield_model_id or "").strip().lower()

        common = {
            "prompt": payload.prompt,
            "duration": payload.durationSeconds,
        }

        if model_id.startswith("wan"):
            return self._build_wan_arguments(common, payload, uploaded_url)

        if model_id.startswith("sora"):
            return self._build_sora_arguments(common, payload, uploaded_url)

        if model_id.startswith("kling"):
            return self._build_kling_arguments(common, payload, uploaded_url)

        return self._build_default_arguments(common, payload, uploaded_url)

    def _build_wan_arguments(
        self,
        common: Dict[str, Any],
        payload: GenerateVideoRequest,
        uploaded_url: str,
    ) -> Dict[str, Any]:
        return {
            **common,
            "image": uploaded_url,
        }

    def _build_sora_arguments(
        self,
        common: Dict[str, Any],
        payload: GenerateVideoRequest,
        uploaded_url: str,
    ) -> Dict[str, Any]:
        return {
            **common,
            "image": uploaded_url,
        }

    def _build_kling_arguments(
        self,
        common: Dict[str, Any],
        payload: GenerateVideoRequest,
        uploaded_url: str,
    ) -> Dict[str, Any]:
        return {
            **common,
            "image": uploaded_url,
        }

    def _build_default_arguments(
        self,
        common: Dict[str, Any],
        payload: GenerateVideoRequest,
        uploaded_url: str,
    ) -> Dict[str, Any]:
        return {
            **common,
            "image": uploaded_url,
        }

    def _submit_job_real(self, arguments: Dict[str, Any]) -> Any:
        if higgsfield_client is None:
            raise RuntimeError("higgsfield-client no está instalado en el entorno.")

        self._build_hf_env()

        return higgsfield_client.submit(
            settings.higgsfield_model_id,
            arguments=arguments,
        )

    def _extract_request_id(self, request_controller: Any) -> str:
        for attr in ("request_id", "id"):
            value = getattr(request_controller, attr, None)
            if value:
                return str(value)

        if isinstance(request_controller, dict):
            for key in ("request_id", "id"):
                if request_controller.get(key):
                    return str(request_controller[key])

        raise RuntimeError("No se pudo extraer request_id desde la respuesta de submit().")

    def _poll_job_real(
        self,
        request_id: str,
        timeout_seconds: int = 300,
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
        if higgsfield_client is None:
            raise RuntimeError("higgsfield-client no está instalado en el entorno.")

        self._build_hf_env()

        result = higgsfield_client.status(request_id=request_id)
        if isinstance(result, dict):
            return result

        return self._status_object_to_dict(result)

    def _get_result_real(self, request_id: str) -> Dict[str, Any]:
        if higgsfield_client is None:
            raise RuntimeError("higgsfield-client no está instalado en el entorno.")

        self._build_hf_env()

        result = higgsfield_client.result(request_id=request_id)
        if isinstance(result, dict):
            return result

        return self._result_object_to_dict(result)

    def _status_object_to_dict(self, status_obj: Any) -> Dict[str, Any]:
        data = {
            "status": status_obj.__class__.__name__.lower(),
        }

        for attr in ("status", "message", "detail", "error", "request_id", "id"):
            value = getattr(status_obj, attr, None)
            if value is not None:
                data[attr] = value

        return data

    def _result_object_to_dict(self, result_obj: Any) -> Dict[str, Any]:
        if isinstance(result_obj, dict):
            return result_obj

        data: Dict[str, Any] = {}
        if hasattr(result_obj, "__dict__"):
            data.update(result_obj.__dict__)

        return data

    def _normalize_provider_status(self, provider_response: Dict[str, Any]) -> str:
        raw_status = str(provider_response.get("status", "")).strip().lower()

        mapping = {
            "queued": "queued",
            "pending": "queued",
            "running": "running",
            "processing": "running",
            "inprogress": "running",
            "in_progress": "running",
            "completed": "succeeded",
            "success": "succeeded",
            "succeeded": "succeeded",
            "failed": "failed",
            "error": "failed",
            "cancelled": "failed",
            "canceled": "failed",
            "nsfw": "failed",
        }

        return mapping.get(raw_status, "running")

    def _extract_error_message(self, provider_response: Dict[str, Any]) -> str:
        for key in ("error", "message", "detail"):
            value = provider_response.get(key)
            if value:
                return str(value)
        return "La generación falló en Higgsfield."

    def _extract_result_url(self, result: Dict[str, Any]) -> Optional[str]:
        candidate_paths = [
            ("video", "url"),
            ("videos", 0, "url"),
            ("output", "url"),
            ("outputs", 0, "url"),
            ("result", "url"),
            ("url",),
        ]

        for path in candidate_paths:
            value = self._dig(result, *path)
            if value:
                return str(value)

        return None

    def _dig(self, data: Any, *path: Any) -> Any:
        current = data
        for key in path:
            if isinstance(key, int):
                if not isinstance(current, list) or key >= len(current):
                    return None
                current = current[key]
            else:
                if not isinstance(current, dict):
                    return None
                current = current.get(key)
                if current is None:
                    return None
        return current

    def _build_video_file_name(self, source_file_name: str) -> str:
        base_name, _sep, _ext = source_file_name.rpartition(".")
        if not base_name:
            base_name = source_file_name
        return f"{base_name}.mp4"

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return task_store.get_task(task_id)


higgsfield_service = HiggsfieldService()