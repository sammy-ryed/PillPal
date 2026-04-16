"""
Text merger — combines OCR results from multiple engines.

Strategy
--------
1. If only one result exists, return it as-is.
2. If both EasyOCR and Tesseract produced results, compare line-by-line.
3. For each line, keep the version from the engine with higher confidence.
4. Overall confidence = weighted mean (EasyOCR weight 0.55, Tesseract 0.45
   — EasyOCR tends to handle handwriting better).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from rapidfuzz.distance import Levenshtein

from app.services.ocr_engine import OCRResult, TextBlock
from app.utils.logger import get_logger

logger = get_logger(__name__)

EASYOCR_WEIGHT = 0.55
TESSERACT_WEIGHT = 0.45


@dataclass
class MergedResult:
    text: str
    avg_confidence: float
    engines_used: List[str]
    primary_engine: str


def merge(results: List[OCRResult]) -> MergedResult:
    """
    Merge one or more OCR results into a single best-effort text output.
    """
    if not results:
        raise ValueError("No OCR results to merge.")

    if len(results) == 1:
        r = results[0]
        return MergedResult(
            text=r.text,
            avg_confidence=r.avg_confidence,
            engines_used=[r.engine],
            primary_engine=r.engine,
        )

    # Partition by engine
    easyocr_res = next((r for r in results if r.engine == "easyocr"), None)
    tesseract_res = next((r for r in results if r.engine == "tesseract"), None)

    if easyocr_res and not tesseract_res:
        primary = easyocr_res
    elif tesseract_res and not easyocr_res:
        primary = tesseract_res
    else:
        # Weighted confidence comparison
        easy_weighted = easyocr_res.avg_confidence * EASYOCR_WEIGHT
        tess_weighted = tesseract_res.avg_confidence * TESSERACT_WEIGHT
        primary = easyocr_res if easy_weighted >= tess_weighted else tesseract_res
        secondary = tesseract_res if primary is easyocr_res else easyocr_res

        merged_text = _line_level_merge(primary, secondary)
        combined_conf = (
            easyocr_res.avg_confidence * EASYOCR_WEIGHT
            + tesseract_res.avg_confidence * TESSERACT_WEIGHT
        )

        logger.debug(
            f"Merged EasyOCR({easyocr_res.avg_confidence:.2f}) + "
            f"Tesseract({tesseract_res.avg_confidence:.2f}) → conf={combined_conf:.2f}"
        )
        return MergedResult(
            text=merged_text,
            avg_confidence=combined_conf,
            engines_used=["easyocr", "tesseract"],
            primary_engine=primary.engine,
        )

    return MergedResult(
        text=primary.text,
        avg_confidence=primary.avg_confidence,
        engines_used=[primary.engine],
        primary_engine=primary.engine,
    )


def _line_level_merge(primary: OCRResult, secondary: OCRResult) -> str:
    """
    Align lines between primary and secondary by rough position,
    keep the higher-confidence version of each line.
    Falls back to primary text if alignment is unreliable.
    """
    primary_lines = [b for b in primary.blocks if b.text.strip()]
    secondary_lines = [b for b in secondary.blocks if b.text.strip()]

    if not secondary_lines:
        return primary.text

    # Match lines by normalised edit distance
    merged: List[str] = []
    used_secondary: set = set()

    for p_block in primary_lines:
        best_match: TextBlock | None = None
        best_sim = 0.0

        for j, s_block in enumerate(secondary_lines):
            if j in used_secondary:
                continue
            sim = _line_similarity(p_block.text, s_block.text)
            if sim > best_sim:
                best_sim = sim
                best_match = s_block
                best_match_idx = j

        # If a good match found and secondary line is more confident
        if best_match and best_sim > 0.5:
            if best_match.confidence > p_block.confidence:
                merged.append(best_match.text)
            else:
                merged.append(p_block.text)
            used_secondary.add(best_match_idx)
        else:
            merged.append(p_block.text)

    return "\n".join(merged)


def _line_similarity(a: str, b: str) -> float:
    """Normalised similarity 0-1 using Levenshtein distance."""
    if not a or not b:
        return 0.0
    dist = Levenshtein.distance(a.lower(), b.lower())
    max_len = max(len(a), len(b))
    return 1.0 - dist / max_len
