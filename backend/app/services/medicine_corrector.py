"""
Medicine name corrector using RapidFuzz.

OCR engines frequently misread characters in medicine names:
  D0l0 650 → Dolo 650
  Metf0rm1n → Metformin
  Pantopraz01e → Pantoprazole

Two-pass correction:
  Pass 1 — OCR character substitution (expand candidates)
  Pass 2 — RapidFuzz token_set_ratio against medicine DB
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, TYPE_CHECKING

from rapidfuzz import fuzz, process

if TYPE_CHECKING:
    from app.services.supabase_service import SupabaseService

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── OCR character substitution table ──────────────────────────────────────────
# Maps common OCR misreads to their likely correct characters.
# Each tuple is (ocr_char, correct_char).
_SUBS: List[Tuple[str, str]] = [
    ("0",  "o"),  # zero → o
    ("1",  "l"),  # one  → l
    ("1",  "i"),  # one  → i
    ("5",  "s"),  # five → s
    ("6",  "g"),  # six  → g (less common but happens)
    ("8",  "b"),  # eight → b
    ("|",  "l"),  # pipe → l
    ("vv", "w"),
    ("rn", "m"),
    ("cl", "d"),
]

# Prefixes that should be stripped before matching
_STRIP_PREFIXES = re.compile(
    r"^\s*(?:tab(?:let)?s?\.?|cap(?:sule)?s?\.?|inj(?:ection)?\.?|syr(?:up)?\.?|"
    r"oint(?:ment)?\.?|drop[s]?\.?|sach(?:et)?s?\.?|susp(?:ension)?\.?|"
    r"gel\.?|cream\.?|lotion\.?|patch\.?|spray\.?)\s+",
    re.IGNORECASE,
)

# Dosage suffix that should be stripped before matching (e.g. "500mg")
_STRIP_DOSAGE = re.compile(
    r"\s+\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|%|mmol)\b.*$",
    re.IGNORECASE,
)


@dataclass
class CorrectionResult:
    original: str
    corrected: str
    score: float      # 0-100
    is_uncertain: bool


class MedicineCorrector:
    """
    Singleton-style: call initialize() at startup, then construct instances.
    """

    _medicine_names: List[str] = []

    @classmethod
    def initialize(cls, svc: "SupabaseService") -> None:
        cls._medicine_names = svc.get_all_medicine_names()
        logger.info(f"MedicineCorrector loaded {len(cls._medicine_names)} medicine names.")

    def __init__(self, threshold: int = 72) -> None:
        self._threshold = threshold

    def correct(self, raw_name: str) -> CorrectionResult:
        """
        Main entry point. Returns the best-matched medicine name.
        """
        if not raw_name or not raw_name.strip():
            return CorrectionResult(raw_name, raw_name, 0.0, True)

        if not self._medicine_names:
            logger.warning("Medicine DB is empty — skipping correction.")
            return CorrectionResult(raw_name, raw_name, 50.0, True)

        # Pre-clean: strip dosage form prefix + dosage suffix
        cleaned = _STRIP_PREFIXES.sub("", raw_name).strip()
        cleaned = _STRIP_DOSAGE.sub("", cleaned).strip()

        if not cleaned:
            cleaned = raw_name

        # Expand with OCR substitution candidates
        candidates = self._generate_candidates(cleaned)

        # Fuzzy match all candidates, keep the best hit
        best_name, best_score, _ = self._best_match(candidates)

        if best_score is None or best_score < self._threshold:
            # Return original (cleaned) but flag as uncertain
            return CorrectionResult(
                original=raw_name,
                corrected=raw_name,
                score=float(best_score or 0),
                is_uncertain=True,
            )

        return CorrectionResult(
            original=raw_name,
            corrected=best_name,
            score=float(best_score),
            is_uncertain=best_score < 85,
        )

    def _generate_candidates(self, text: str) -> List[str]:
        """
        Apply each substitution independently to generate alternative spellings.
        Returns the original plus up to N variants.
        """
        candidates = {text}
        lower = text.lower()

        for bad, good in _SUBS:
            if bad in lower:
                variant = lower.replace(bad, good, 1)
                candidates.add(variant)
                # Also try replacing all occurrences
                candidates.add(lower.replace(bad, good))

        return list(candidates)

    def _best_match(
        self, candidates: List[str]
    ) -> Tuple[str, Optional[float], str]:
        best_name = ""
        best_score: Optional[float] = None

        for candidate in candidates:
            match = process.extractOne(
                candidate,
                self._medicine_names,
                scorer=fuzz.token_set_ratio,
                score_cutoff=0,
            )
            if match:
                name, score, _ = match
                if best_score is None or score > best_score:
                    best_score = score
                    best_name = name

        return best_name, best_score, ""
