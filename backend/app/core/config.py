from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

DB_PATH_DEFAULT = PROJECT_ROOT / "database" / "lottery.sqlite"
HISTORY_CSV_PATH_DEFAULT = PROJECT_ROOT / "database" / "dataset" / "lottery_history.csv"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="LOTTERY_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Lottery Foundation API"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    db_path: str = str(DB_PATH_DEFAULT)
    history_csv_path: str = str(HISTORY_CSV_PATH_DEFAULT)
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
