"""
Prescription router.

POST /api/prescriptions/parse     — Upload image, run full pipeline
POST /api/prescriptions/reminders — Generate reminder plan from confirmed meds
GET  /api/medicines               — List all medicines in DB (with optional ?q= search)
"""
from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.models.prescription import MedicineEntry, PrescriptionResult
from app.models.reminder import ReminderPlan
from app.services.image_preprocessor import ImagePreprocessor
from app.services.medicine_corrector import MedicineCorrector
from app.services.ocr_engine import OCREngineManager
from app.services.prescription_parser import PrescriptionParser
from app.services.reminder_generator import ReminderGenerator
from app.services.supabase_service import get_supabase_service
from app.services.text_merger import merge
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["prescriptions"])

# Shared thread pool for CPU-bound OCR work
_executor = ThreadPoolExecutor(max_workers=2)

# Module-level instances (stateless — safe to share)
_preprocessor = ImagePreprocessor()
_reminder_gen = ReminderGenerator()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}


def _run_pipeline(image_bytes: bytes, settings: Settings) -> PrescriptionResult:
    """
    Full OCR pipeline. Runs in a thread pool to avoid blocking the event loop.
    """
    start = time.perf_counter()

    # Stage 1: Image preprocessing
    variants = _preprocessor.preprocess(image_bytes)

    # Image quality score (based on primary variant)
    import cv2, numpy as np
    gray = cv2.cvtColor(variants[0].image if len(variants[0].image.shape) == 3
                        else np.stack([variants[0].image]*3, axis=-1),
                        cv2.COLOR_BGR2GRAY) if len(variants[0].image.shape) == 3 else variants[0].image
    quality = _preprocessor.quality_score(gray)

    # Stage 2: OCR
    engine_mgr = OCREngineManager(
        use_easyocr=settings.use_easyocr,
        use_tesseract=settings.use_tesseract,
    )
    ocr_results = engine_mgr.run(variants)

    if not ocr_results:
        raise RuntimeError("All OCR engines failed. Check Tesseract installation.")

    # Stage 3: Merge OCR outputs
    merged = merge(ocr_results)

    logger.info(
        f"OCR merged: engines={merged.engines_used} "
        f"conf={merged.avg_confidence:.2f} text_len={len(merged.text)}"
    )

    # Stage 4 + 5 + 6: Parse, correct, frequency, reminder times
    parser = PrescriptionParser(threshold=settings.ocr_confidence_threshold)
    result = parser.parse(
        merged=merged,
        preprocessing_variants=[v.name for v in variants],
        image_quality=quality,
        start_time=start,
    )

    return result


@router.post("/parse", response_model=PrescriptionResult)
async def parse_prescription(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> PrescriptionResult:
    """
    Upload a prescription image. Returns structured JSON with extracted medicines.
    """
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Accepted: JPEG, PNG, WEBP, BMP, TIFF.",
        )

    image_bytes = await file.read()

    # Validate size
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB.",
        )

    if len(image_bytes) < 1000:
        raise HTTPException(status_code=400, detail="File is too small or corrupt.")

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor, _run_pipeline, image_bytes, settings
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"Pipeline error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Prescription processing failed. Please try again with a clearer image.",
        )

    # Persist to Supabase asynchronously (non-blocking — failure doesn't break response)
    try:
        svc = get_supabase_service()
        prescription_id = await svc.save_prescription(result.model_dump(mode="json"))
        result.id = prescription_id
    except Exception as exc:
        logger.warning(f"Could not persist prescription: {exc}")

    return result


class RemindersRequest(PrescriptionResult):
    """Accepts confirmed prescription result to generate a reminder plan."""
    pass


@router.post("/reminders", response_model=ReminderPlan)
async def generate_reminders(payload: PrescriptionResult) -> ReminderPlan:
    """
    Given a confirmed (possibly user-edited) prescription result,
    generate the full reminder schedule.
    """
    plan = _reminder_gen.generate(
        medicines=payload.medicines,
        prescription_id=payload.id,
    )

    try:
        svc = get_supabase_service()
        await svc.save_reminders(payload.id or "", plan.model_dump(mode="json"))
    except Exception as exc:
        logger.warning(f"Could not persist reminders: {exc}")

    return plan


# ── Medicine lookup ────────────────────────────────────────────────────────────

@router.get("/medicines", response_model=List[str])
async def list_medicines(
    q: Optional[str] = Query(default=None, description="Filter by name prefix/substring"),
    limit: int = Query(default=100, ge=1, le=500, description="Max results"),
) -> List[str]:
    """
    Return all medicine names in the DB.
    Optionally filter with ?q=metf to find medicines matching 'metf'.
    Useful for frontend autocomplete and validation.
    """
    try:
        svc = get_supabase_service()
        names = svc.get_all_medicine_names()
    except Exception:
        names = []

    if q:
        q_lower = q.lower()
        names = [n for n in names if q_lower in n.lower()]

    return names[:limit]


@router.get("/medicines/count")
async def medicine_count() -> dict:
    """Return count of medicines in the DB."""
    try:
        svc = get_supabase_service()
        names = svc.get_all_medicine_names()
        return {"count": len(names), "source": "database"}
    except Exception:
        return {"count": 0, "source": "error"}
