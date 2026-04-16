"""
Health check router.
Exposes: GET /api/health
"""
from fastapi import APIRouter
from app.services.medicine_corrector import MedicineCorrector
from app.services.frequency_parser import FrequencyParser

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "medicine_db_size": len(MedicineCorrector._medicine_names),
        "frequency_codes_loaded": len(FrequencyParser._codes),
    }
