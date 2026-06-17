import os
from pydantic_settings import BaseSettings

# Determine safe data directory based on OS for deployment compatibility
if os.name == 'nt':
    APP_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "TransactIQ")
else:
    APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

os.makedirs(APP_DIR, exist_ok=True)

_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
_DB_PATH = os.path.join(APP_DIR, "transactiq.db").replace("\\", "/")


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{_DB_PATH}"
    upload_dir: str = os.path.join(APP_DIR, "uploads")
    output_dir: str = os.path.join(APP_DIR, "outputs")
    frontend_url: str = "http://localhost:3000"
    openai_api_key: str = ""

    class Config:
        env_file = _ENV_FILE


settings = Settings()
