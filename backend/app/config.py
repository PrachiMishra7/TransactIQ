from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/transactiq"
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    frontend_url: str = "http://localhost:3000"
    openai_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
