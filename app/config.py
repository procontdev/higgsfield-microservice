import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.port: int = int(os.getenv("PORT", "3010"))
        self.app_env: str = os.getenv("APP_ENV", "development")
        self.active_video_provider: str = os.getenv("ACTIVE_VIDEO_PROVIDER", "higgsfield").strip().lower()

        self.higgsfield_api_key: str = os.getenv("HIGGSFIELD_API_KEY", "").strip()
        self.higgsfield_api_secret: str = os.getenv("HIGGSFIELD_API_SECRET", "").strip()
        self.higgsfield_model_id: str = os.getenv("HIGGSFIELD_MODEL_ID", "").strip()

        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    @property
    def hf_key(self) -> str:
        """
        Formato compatible con el SDK oficial:
        HF_KEY=api_key:api_secret
        """
        if self.higgsfield_api_key and self.higgsfield_api_secret:
            return f"{self.higgsfield_api_key}:{self.higgsfield_api_secret}"
        return ""


settings = Settings()