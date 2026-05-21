from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""
    race_master_user_id: int = 0

    database_url: str = "sqlite+aiosqlite:///./heritage_trail.db"
    dashboard_port: int = 3001
    backend_port: int = 8000

    vision_api_key: str = ""
    vision_model: str = "glm-4v-flash"

    gdrive_client_id: str = ""
    gdrive_client_secret: str = ""
    gdrive_refresh_token: str = ""
    gdrive_folder_id: str = ""

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
