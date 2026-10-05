from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "FitDesk Fitness Class & Membership Manager"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = f"sqlite:///{(BACKEND_DIR / 'fitdesk.db').as_posix()}"
    AUTH_DATABASE_URL: str = f"sqlite:///{(BACKEND_DIR / 'fitdesk-auth.db').as_posix()}"
    JWT_SECRET_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Demo staff credentials for deployed application
    DEMO_ADMIN_PASSWORD: Optional[str] = None
    DEMO_TRAINER_PASSWORD: Optional[str] = None

    # Allowed CORS origins for frontend client (e.g. Vite default port)
    BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://frontend-rsnd.onrender.com",
]

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
