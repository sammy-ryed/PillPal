"""
Dual OCR engine wrapper.

EasyOCR  — stronger on handwriting, no Tesseract dependency.
Tesseract — faster, strong on printed text, per-word confidence.

Both implement the OCREngine protocol (duck-typed).
OCREngineManager runs both across all preprocessing variants,
picks the highest-confidence result per engine, and returns them
for the text merger to resolve.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from app.services.image_preprocessor import ProcessedVariant
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TextBlock:
    text: str
    confidence: float       # 0.0 – 1.0
    line_num: int


@dataclass
class OCRResult:
    engine: str
    variant_name: str
    text: str               # Full merged text
    blocks: List[TextBlock]
    avg_confidence: float
    elapsed_ms: float


# ── EasyOCR ───────────────────────────────────────────────────────────────────

class EasyOCREngine:
    """
    Lazy-initialised EasyOCR reader (English).
    GPU used if CUDA is available, falls back to CPU silently.

    Singleton: instantiated ONCE at module level so the model
    is loaded only on the first request, not on every upload.
    """

    def __init__(self) -> None:
        self._reader = None

    @property
    def reader(self):
        if self._reader is None:
            import easyocr
            logger.info("Initialising EasyOCR reader (first call only)…")
            self._reader = easyocr.Reader(
                ["en"],
                gpu=self._has_gpu(),
                verbose=False,
            )
        return self._reader

    @staticmethod
    def _has_gpu() -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    # ── BUG FIX: merge same-row bounding boxes ────────────────────────────────
    def _merge_into_lines(
        self, detections: list
    ) -> List[Tuple[str, float]]:
        """
        EasyOCR with paragraph=False returns one entry per text *region*.
        On prescriptions the indented layout causes it to split a single
        medicine line like:
            "Tab Metformin"   (box 1)
            "40mg  1-0-0"     (box 2)
        into two separate detections with different x-offsets but nearly
        the same y-centre.  We group boxes whose y-centres are within
        ~70 % of the average line height, sort them left-to-right, and
        concatenate the texts.

        Returns list of (merged_text, avg_confidence) — one item per row.
        """
        if not detections:
            return []

        items = []
        for bbox, text, conf in detections:
            if not text.strip():
                continue
            y_vals = [p[1] for p in bbox]
            x_vals = [p[0] for p in bbox]
            items.append({
                "text": text.strip(),
                "conf": float(conf),
                "y_center": sum(y_vals) / len(y_vals),
                "y_top":    min(y_vals),
                "y_bot":    max(y_vals),
                "x_left":   min(x_vals),
                "height":   max(y_vals) - min(y_vals) + 1,
            })

        if not items:
            return []

        # Sort by y_center, then x_left
        items.sort(key=lambda x: (x["y_center"], x["x_left"]))

        rows: List[List[dict]] = []
        current_row = [items[0]]

        for item in items[1:]:
            last = current_row[-1]
            avg_h = (item["height"] + last["height"]) / 2
            if avg_h < 4:
                avg_h = 14  # minimum sensible line height (pixels)
            if abs(item["y_center"] - last["y_center"]) <= avg_h * 0.7:
                current_row.append(item)
            else:
                rows.append(current_row)
                current_row = [item]
        rows.append(current_row)

        merged: List[Tuple[str, float]] = []
        for row in rows:
            row.sort(key=lambda x: x["x_left"])
            text = " ".join(x["text"] for x in row)
            avg_conf = sum(x["conf"] for x in row) / len(row)
            merged.append((text, avg_conf))

        return merged

    def extract(self, variant: ProcessedVariant) -> Optional[OCRResult]:
        try:
            start = time.perf_counter()
            raw = self.reader.readtext(variant.image, detail=1, paragraph=False)
            elapsed = (time.perf_counter() - start) * 1000

            # Merge same-row boxes before creating TextBlocks
            merged_lines = self._merge_into_lines(raw)

            blocks: List[TextBlock] = []
            for i, (text, conf) in enumerate(merged_lines):
                if text:
                    blocks.append(TextBlock(text=text, confidence=conf, line_num=i))

            full_text = "\n".join(b.text for b in blocks if b.text)
            avg_conf = float(np.mean([b.confidence for b in blocks])) if blocks else 0.0

            logger.debug(f"EasyOCR [{variant.name}] lines={len(blocks)} conf={avg_conf:.2f} t={elapsed:.0f}ms")
            return OCRResult(
                engine="easyocr",
                variant_name=variant.name,
                text=full_text,
                blocks=blocks,
                avg_confidence=avg_conf,
                elapsed_ms=elapsed,
            )
        except Exception as exc:
            logger.error(f"EasyOCR failed on variant {variant.name}: {exc}")
            return None


# ── Tesseract ──────────────────────────────────────────────────────────────────

class TesseractEngine:
    """
    pytesseract wrapper.
    PSM 6 = uniform block of text (best for prescription body).
    Returns per-word confidence data for the text merger.
    """

    # OEM 3 = LSTM + legacy; PSM 6 = assume uniform text block
    _CONFIG_BLOCK  = "--oem 3 --psm 6"
    _CONFIG_SPARSE = "--oem 3 --psm 11"  # sparse text — fallback

    def extract(self, variant: ProcessedVariant) -> Optional[OCRResult]:
        try:
            import pytesseract
            start = time.perf_counter()

            data = pytesseract.image_to_data(
                variant.pil_image,
                config=self._CONFIG_BLOCK,
                output_type=pytesseract.Output.DICT,
            )
            elapsed = (time.perf_counter() - start) * 1000

            blocks: List[TextBlock] = []
            current_line = -1
            line_texts: List[str] = []
            line_confs: List[float] = []

            for i, word in enumerate(data["text"]):
                word = word.strip()
                conf = int(data["conf"][i])
                line_num = data["line_num"][i]

                if conf < 0 or not word:
                    continue

                norm_conf = conf / 100.0
                if line_num != current_line:
                    if current_line != -1 and line_texts:
                        avg = float(np.mean(line_confs))
                        blocks.append(TextBlock(
                            text=" ".join(line_texts),
                            confidence=avg,
                            line_num=current_line,
                        ))
                    line_texts = [word]
                    line_confs = [norm_conf]
                    current_line = line_num
                else:
                    line_texts.append(word)
                    line_confs.append(norm_conf)

            if line_texts:
                blocks.append(TextBlock(
                    text=" ".join(line_texts),
                    confidence=float(np.mean(line_confs)),
                    line_num=current_line,
                ))

            full_text = "\n".join(b.text for b in blocks if b.text)
            avg_conf = float(np.mean([b.confidence for b in blocks])) if blocks else 0.0

            logger.debug(f"Tesseract [{variant.name}] lines={len(blocks)} conf={avg_conf:.2f} t={elapsed:.0f}ms")
            return OCRResult(
                engine="tesseract",
                variant_name=variant.name,
                text=full_text,
                blocks=blocks,
                avg_confidence=avg_conf,
                elapsed_ms=elapsed,
            )
        except Exception as exc:
            logger.error(f"Tesseract failed on variant {variant.name}: {exc}")
            return None


# ── Singleton engines (shared across requests) ────────────────────────────────
# EasyOCREngine is created ONCE here so the model is downloaded and cached
# on the first request rather than re-initialised on every upload.

_easyocr_singleton = EasyOCREngine()
_tesseract_singleton = TesseractEngine()


# ── Manager ────────────────────────────────────────────────────────────────────

class OCREngineManager:
    """
    Runs all configured OCR engines across ALL preprocessing variants.
    Picks the HIGHEST-confidence result per engine (not just the first one
    that passes 0.1) and returns them for the text merger to resolve.
    """

    def __init__(self, use_easyocr: bool = True, use_tesseract: bool = True) -> None:
        self._engines = []
        if use_easyocr:
            self._engines.append(_easyocr_singleton)
        if use_tesseract:
            self._engines.append(_tesseract_singleton)

        if not self._engines:
            raise RuntimeError("No OCR engines configured. Enable at least one in settings.")

    def run(self, variants: List[ProcessedVariant]) -> List[OCRResult]:
        """
        Tries ALL variants per engine and keeps the one with the
        highest avg_confidence — ensuring the best preprocessing
        result is always selected.
        """
        results: List[OCRResult] = []

        for engine in self._engines:
            best: Optional[OCRResult] = None
            for variant in variants:
                r = engine.extract(variant)
                if r and (best is None or r.avg_confidence > best.avg_confidence):
                    best = r

            if best:
                logger.info(
                    f"{best.engine}: best variant={best.variant_name} "
                    f"conf={best.avg_confidence:.2f} lines={len(best.blocks)}"
                )
                results.append(best)

        return results
