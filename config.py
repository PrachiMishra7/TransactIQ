import os
from pydantic_settings import BaseSettings

# Resolve .env path relative to this file — works regardless of CWD
_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev.db").replace("\\", "/")


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{_DB_PATH}"
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    frontend_url: str = "http://localhost:3000"
    openai_api_key: str = ""

    class Config:
        env_file = _ENV_FILE


settings = Settings()
