"""
Optional Donut-based OCR fallback.

This module is intentionally defensive:
- It is used only when explicitly enabled in settings.
- Imports for heavy dependencies (torch/transformers) are lazy.
- Any loading/inference failure returns None and does not break the main OCR path.
"""
from __future__ import annotations

import io
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from PIL import Image

from app.utils.logger import get_logger

logger = get_logger(__name__)

_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")

_MED_NAME_KEYS = ("medicine_name", "medicine", "drug_name", "drug", "name")
_DOSAGE_KEYS = ("dosage", "dose", "strength")
_FREQ_KEYS = ("frequency", "frequency_code", "freq", "schedule")
_DURATION_KEYS = ("duration", "duration_days", "days")
_NOTE_KEYS = ("timing_note", "timing_notes", "instructions", "instruction", "note")


@dataclass
class DonutFallbackResult:
    text: str
    raw_output: str
    model_id: str
    elapsed_ms: float


def _normalise_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _dict_to_medicine_line(payload: Dict[str, Any]) -> str:
    def pick(keys: tuple[str, ...]) -> str:
        for key in keys:
            value = payload.get(key)
            if value is None:
                continue
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    parts = [
        pick(_MED_NAME_KEYS),
        pick(_DOSAGE_KEYS),
        pick(_FREQ_KEYS),
        pick(_DURATION_KEYS),
        pick(_NOTE_KEYS),
    ]
    return _normalise_ws(" ".join(p for p in parts if p))


def _json_to_lines(payload: Any) -> List[str]:
    """Convert common Donut JSON-like outputs into line-oriented text."""
    lines: List[str] = []

    if isinstance(payload, list):
        for item in payload:
            lines.extend(_json_to_lines(item))
        return lines

    if isinstance(payload, dict):
        # Common pattern: medicines is a list of dict entries.
        meds = payload.get("medicines")
        if isinstance(meds, list):
            for med in meds:
                if isinstance(med, dict):
                    line = _dict_to_medicine_line(med)
                    if line:
                        lines.append(line)
                elif isinstance(med, str) and med.strip():
                    lines.append(_normalise_ws(med))
            return lines

        line = _dict_to_medicine_line(payload)
        if line:
            lines.append(line)
            return lines

        # Generic fallback: recursively consume nested fields.
        for value in payload.values():
            lines.extend(_json_to_lines(value))
        return lines

    if isinstance(payload, str):
        clean = _normalise_ws(payload)
        if clean:
            lines.append(clean)

    return lines


class DonutFallbackEngine:
    def __init__(self) -> None:
        self._processor = None
        self._model = None
        self._device = "cpu"
        self._model_id = ""
        self._load_error_logged = False
        self._deps_missing = False

    def _ensure_loaded(self, model_id: str, hf_token: str | None = None) -> bool:
        if self._processor is not None and self._model is not None and self._model_id == model_id:
            return True

        if self._deps_missing:
            return False

        try:
            import torch
            from transformers import DonutProcessor, VisionEncoderDecoderModel
        except Exception as exc:
            if not self._load_error_logged:
                logger.warning(
                    "Donut fallback disabled at runtime: missing dependencies "
                    "(install torch, transformers, sentencepiece). Error: %s",
                    exc,
                )
                self._load_error_logged = True
            self._deps_missing = True
            return False

        try:
            logger.info("Loading Donut fallback model: %s", model_id)
            token = (hf_token or "").strip() or None
            self._processor = DonutProcessor.from_pretrained(model_id, token=token)
            self._model = VisionEncoderDecoderModel.from_pretrained(model_id, token=token)
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model.to(self._device)
            self._model_id = model_id
            self._load_error_logged = False
            self._deps_missing = False
            return True
        except Exception as exc:
            logger.warning("Could not load Donut fallback model '%s': %s", model_id, exc)
            return False

    def extract(
        self,
        image_bytes: bytes,
        model_id: str,
        max_length: int = 512,
        hf_token: str | None = None,
    ) -> Optional[DonutFallbackResult]:
        if not self._ensure_loaded(model_id, hf_token):
            return None

        try:
            import torch

            start = time.perf_counter()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            pixel_values = self._processor(images=image, return_tensors="pt").pixel_values.to(self._device)
            decoder_input_ids = self._processor.tokenizer(
                "<s_ocr>", return_tensors="pt"
            ).input_ids.to(self._device)

            with torch.no_grad():
                generated_ids = self._model.generate(
                    pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    max_length=max_length,
                    num_beams=1,
                    early_stopping=True,
                )

            raw = self._processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
            text = self._normalise_output(raw)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if not text.strip():
                return None

            return DonutFallbackResult(
                text=text,
                raw_output=raw,
                model_id=model_id,
                elapsed_ms=elapsed_ms,
            )
        except Exception as exc:
            logger.warning("Donut fallback inference failed: %s", exc)
            return None

    def _normalise_output(self, raw: str) -> str:
        clean = raw.strip()

        # Try JSON extraction first if model emitted structured output.
        m = _JSON_BLOCK_RE.search(clean)
        if m:
            try:
                payload = json.loads(m.group(0))
                lines = _json_to_lines(payload)
                lines = [line for line in lines if len(line) >= 3]
                if lines:
                    return "\n".join(lines)
            except Exception:
                pass

        # Handle Donut-style tags into line-like text.
        clean = re.sub(r"</s_[^>]+>", "\n", clean)
        clean = re.sub(r"<s_[^>]+>", " ", clean)
        clean = clean.replace("<sep/>", "\n")
        clean = re.sub(r"<[^>]+>", " ", clean)
        clean = clean.replace(";", "\n")

        lines = [_normalise_ws(line) for line in clean.splitlines()]
        lines = [line for line in lines if len(line) >= 3]
        return "\n".join(lines)


_instance: Optional[DonutFallbackEngine] = None


def get_donut_fallback_engine() -> DonutFallbackEngine:
    global _instance
    if _instance is None:
        _instance = DonutFallbackEngine()
    return _instance
