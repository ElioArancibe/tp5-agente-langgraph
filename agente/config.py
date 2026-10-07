import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    api_key: SecretStr
    model: str = "gemini-3.5-flash"
    fallback_model: str | None = "gemini-3.5-flash-lite"
    temperature: float = Field(default=0, ge=0, le=2)
    recursion_limit: int = Field(default=10, ge=4, le=50)
    max_historial: int = Field(default=30, ge=4)

    tienda_db: Path = BASE_DIR / "data" / "tienda.db"
    memoria_db: Path = BASE_DIR / "data" / "memoria.db"
    trazas_dir: Path = BASE_DIR / "trazas"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(BASE_DIR / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el .env (ver .env.example).")

    overrides = {
        "model": os.getenv("GEMINI_MODEL"),
        "fallback_model": os.getenv("GEMINI_FALLBACK_MODEL"),
        "recursion_limit": os.getenv("RECURSION_LIMIT"),
    }
    return Settings(api_key=api_key, **{k: v for k, v in overrides.items() if v})
