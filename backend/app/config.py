"""PayShield AI – application settings (pydantic-settings)."""

from __future__ import annotations

import json
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Loaded from environment variables / .env file."""

    # Database
    DB_URL: str = "sqlite:///payshield.db"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Model / version
    MODEL_VERSION: str = "0.1.0-rules"
    ML_MODEL_ENABLED: bool = True
    ML_MODEL_DIR: Optional[str] = None

    # Risk thresholds
    THRESHOLD_LOW_MAX: int = 39
    THRESHOLD_MEDIUM_MAX: int = 69
    # HIGH is 70-100 implicitly

    # Graph thresholds
    FAN_IN_MIN: int = 4
    FAN_OUT_MIN: int = 3
    RAPID_ONWARD_MINUTES: int = 15

    # Paths
    SEED_PATH: str = "app/data/seed.json"
    SNAPSHOT_PATH: str = "app/data/fallback/payshield_snapshot.db"

    # Admin
    ENABLE_ADMIN: bool = True
    ENABLE_SIMULATED_CALLBACKS: bool = True

    # LLM & AI Explainer
    GEMINI_API_KEY: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_TIMEOUT_SECONDS: float = 5.0

    # Disclaimer
    DISCLAIMER: str = (
        "Prototype using synthetic data. "
        "Risk scores are illustrative heuristics, not proof of fraud."
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
