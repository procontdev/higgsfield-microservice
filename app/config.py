import os
from dotenv import load_dotenv

load_dotenv()


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.port: int = int(os.getenv("PORT", "3010"))
        self.app_env: str = os.getenv("APP_ENV", "development")
        self.active_video_provider: str = os.getenv("ACTIVE_VIDEO_PROVIDER", "higgsfield").strip().lower()

        self.higgsfield_api_key: str = os.getenv("HIGGSFIELD_API_KEY", "").strip()
        self.higgsfield_api_secret: str = os.getenv("HIGGSFIELD_API_SECRET", "").strip()

        self.higgsfield_model_id: str = os.getenv("HIGGSFIELD_MODEL_ID", "").strip()
        self.higgsfield_model_label: str = os.getenv("HIGGSFIELD_MODEL_LABEL", "").strip()

        self.higgsfield_execution_enabled: bool = _to_bool(
            os.getenv("HIGGSFIELD_EXECUTION_ENABLED", "false"),
            default=False,
        )

        self.higgsfield_test_mode: bool = _to_bool(
            os.getenv("HIGGSFIELD_TEST_MODE", "true"),
            default=True,
        )

        self.higgsfield_allowed_job_id: str = os.getenv("HIGGSFIELD_ALLOWED_JOB_ID", "").strip()
        self.higgsfield_max_duration_seconds: int = int(
            os.getenv("HIGGSFIELD_MAX_DURATION_SECONDS", "4")
        )

        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    @property
    def hf_key(self) -> str:
        if self.higgsfield_api_key and self.higgsfield_api_secret:
            return f"{self.higgsfield_api_key}:{self.higgsfield_api_secret}"
        return ""

    @property
    def model_configured(self) -> bool:
        return bool(self.higgsfield_model_id)

    @property
    def credentials_configured(self) -> bool:
        return bool(self.higgsfield_api_key and self.higgsfield_api_secret)

    @property
    def model_display_name(self) -> str:
        if self.higgsfield_model_label:
            return self.higgsfield_model_label
        if self.higgsfield_model_id:
            return self.higgsfield_model_id
        return "not-configured"


settings = Settings()