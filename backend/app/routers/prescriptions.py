"""
Prescription router.

POST /api/prescriptions/parse     — Upload image, run full pipeline
POST /api/prescriptions/reminders — Generate reminder plan from confirmed meds
GET  /api/medicines               — List all medicines in DB (with optional ?q= search)
"""
from __future__ import annotations

import asyncio
import hashlib
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.models.prescription import MedicineEntry, PrescriptionResult
from app.models.reminder import ReminderPlan
from app.services.donut_ocr import get_donut_fallback_engine
from app.services.image_preprocessor import ImagePreprocessor
from app.services.medicine_corrector import MedicineCorrector
from app.services.ocr_engine import OCREngineManager
from app.services.prescription_parser import PrescriptionParser
from app.services.reminder_generator import ReminderGenerator
from app.services.supabase_service import get_supabase_service
from app.services.text_merger import MergedResult, merge
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["prescriptions"])

# Shared thread pool for CPU-bound OCR work
_executor = ThreadPoolExecutor(max_workers=2)

# Module-level instances (stateless — safe to share)
_preprocessor = ImagePreprocessor()
_reminder_gen = ReminderGenerator()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}

_PIPELINE_CACHE: "OrderedDict[str, dict]" = OrderedDict()
_PIPELINE_CACHE_LOCK = Lock()


def _make_cache_key(image_bytes: bytes, settings: Settings) -> str:
    sig = "|".join(
        [
            str(settings.use_easyocr),
            str(settings.use_tesseract),
            str(settings.use_donut_fallback),
            str(settings.ocr_fast_mode),
            str(settings.ocr_max_variants_per_engine),
            str(settings.ocr_early_stop_confidence),
            str(settings.ocr_skip_tesseract_confidence),
            str(settings.ocr_confidence_threshold),
            str(settings.donut_fallback_trigger_confidence),
            settings.donut_model_id,
        ]
    )
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    settings_hash = hashlib.sha1(sig.encode("utf-8")).hexdigest()
    return f"{image_hash}:{settings_hash}"


def _cache_get_result(cache_key: str) -> Optional[PrescriptionResult]:
    with _PIPELINE_CACHE_LOCK:
        payload = _PIPELINE_CACHE.get(cache_key)
        if payload is None:
            return None
        _PIPELINE_CACHE.move_to_end(cache_key)
    return PrescriptionResult.model_validate(payload)


def _cache_put_result(cache_key: str, result: PrescriptionResult, max_size: int) -> None:
    payload = result.model_dump(mode="json")
    with _PIPELINE_CACHE_LOCK:
        _PIPELINE_CACHE[cache_key] = payload
        _PIPELINE_CACHE.move_to_end(cache_key)
        while len(_PIPELINE_CACHE) > max_size:
            _PIPELINE_CACHE.popitem(last=False)


def _result_rank(result: PrescriptionResult) -> tuple[int, int, float]:
    """
    Rank parsed results by usefulness:
    1) more medicines, 2) more certain medicines, 3) higher confidence.
    """
    total = len(result.medicines)
    uncertain = sum(1 for med in result.medicines if med.is_uncertain)
    certain = total - uncertain
    return (total, certain, result.overall_confidence)


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
        fast_mode=settings.ocr_fast_mode,
        max_variants_per_engine=settings.ocr_max_variants_per_engine,
        early_stop_confidence=settings.ocr_early_stop_confidence,
        skip_tesseract_confidence=settings.ocr_skip_tesseract_confidence,
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

    uncertain_ratio = (
        (sum(1 for med in result.medicines if med.is_uncertain) / len(result.medicines))
        if result.medicines
        else 1.0
    )

    should_try_donut = (
        settings.use_donut_fallback
        and (
            not result.medicines
            or result.overall_confidence <= settings.donut_fallback_trigger_confidence
            or uncertain_ratio >= 0.80
        )
    )

    if should_try_donut:
        donut_engine = get_donut_fallback_engine()
        donut = donut_engine.extract(
            image_bytes=image_bytes,
            model_id=settings.donut_model_id,
            max_length=settings.donut_max_length,
            hf_token=settings.hf_token,
        )

        if donut and donut.text.strip():
            logger.info(
                f"Trying Donut fallback: model={donut.model_id} "
                f"text_len={len(donut.text)} t={donut.elapsed_ms:.0f}ms"
            )

            donut_merged = MergedResult(
                text=donut.text,
                avg_confidence=max(result.overall_confidence, settings.donut_assumed_confidence),
                engines_used=["donut"],
                primary_engine="donut",
            )

            donut_result = parser.parse(
                merged=donut_merged,
                preprocessing_variants=[v.name for v in variants] + ["donut_fallback"],
                image_quality=quality,
                start_time=start,
            )

            if _result_rank(donut_result) > _result_rank(result):
                donut_result.warnings.append(
                    "Donut fallback OCR was used to recover low-confidence handwriting. "
                    "Please review medicines before confirming reminders."
                )
                result = donut_result
                logger.info(
                    f"Donut fallback selected: meds={len(result.medicines)} "
                    f"conf={result.overall_confidence:.2f}"
                )
            else:
                logger.info("Donut fallback did not improve extraction; keeping primary OCR result.")

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

    cache_key = ""
    if settings.enable_parse_cache:
        cache_key = _make_cache_key(image_bytes, settings)
        cached = _cache_get_result(cache_key)
        if cached is not None:
            logger.info(
                f"Parse cache hit: key={cache_key[:12]} meds={len(cached.medicines)} "
                f"conf={cached.overall_confidence:.2f}"
            )
            result = cached
        else:
            result = None
    else:
        result = None

    if result is None:
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

        if settings.enable_parse_cache and cache_key:
            _cache_put_result(cache_key, result, settings.parse_cache_size)

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
