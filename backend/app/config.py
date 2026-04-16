"""
Application configuration.
All secrets and toggles come from .env — nothing hardcoded.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PillPal API"
    debug: bool = False

    # ── Supabase ──────────────────────────────────────────────────────────────
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_key: str = Field(default="", description="Supabase anon/service key")

    # ── OCR engines ───────────────────────────────────────────────────────────
    use_easyocr: bool = True
    use_tesseract: bool = True
    # Optional transformer-based fallback for difficult handwriting
    use_donut_fallback: bool = True
    donut_fallback_trigger_confidence: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Trigger Donut fallback when overall OCR confidence drops below this value",
    )
    donut_model_id: str = Field(
        default="chinmays18/medical-prescription-ocr",
        description="Hugging Face model id for optional Donut fallback OCR",
    )
    donut_max_length: int = Field(default=512, ge=64, le=2048)
    donut_assumed_confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    hf_token: str = Field(
        default="",
        description="Optional Hugging Face access token for higher Hub rate limits and faster model downloads",
    )

    # ── Confidence thresholds ─────────────────────────────────────────────────
    # Below this → OCR result is considered unreliable
    ocr_confidence_threshold: float = 0.45
    # RapidFuzz score (0-100) below which medicine match is flagged uncertain
    medicine_match_threshold: int = 72
    # Below this → warnings["Low OCR confidence"] is added
    low_confidence_warning_threshold: float = 0.60

    # ── Upload ────────────────────────────────────────────────────────────────
    max_upload_size_mb: int = 10

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: List[str] = ["*"]

    # ── Reminder time defaults ────────────────────────────────────────────────
    morning_time: str = "08:00"
    lunch_time: str = "13:00"
    evening_time: str = "18:00"
    dinner_time: str = "20:00"
    bedtime_time: str = "22:00"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
