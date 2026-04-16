"""
Prescription text parser.

Takes raw OCR text and converts it into a structured list of MedicineEntry
objects, plus metadata (doctor name, patient name, date).

Approach
--------
1. Split text into lines.
2. Score each line for "medicine-likeness" using feature heuristics.
3. High-scoring lines are parsed as medicine entries.
4. For each entry: extract dosage → frequency → duration → timing → name.
5. Apply MedicineCorrector and FrequencyParser to each entry.

This uses a residual extraction strategy: repeatedly strip known patterns
from the line until what remains is the medicine name candidate.
"""
from __future__ import annotations

import re
import time
from typing import List, Optional, Tuple

from app.models.prescription import MedicineEntry, PrescriptionResult, ProcessingMetadata
from app.services.medicine_corrector import MedicineCorrector
from app.services.frequency_parser import FrequencyParser
from app.services.text_merger import MergedResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Regex patterns ─────────────────────────────────────────────────────────────

# Dosage: 500mg, 40 mg, 1.5g, 60,000 IU, 0.5%, 10ml
_DOSAGE_RE = re.compile(
    r"\b(\d[\d,]*(?:\.\d+)?)\s*(mg|mcg|g\b|ml|iu|gm|mmol|meq|%)\b",
    re.IGNORECASE,
)

# Duration: "5 days", "2 weeks", "1 month", "x5", "for 10 days", "5/7"
_DURATION_PATTERNS = [
    re.compile(r"x\s*(\d+)\s*(?:day|d\b)", re.IGNORECASE),
    re.compile(r"(?:for\s+)?(\d+)\s*day(?:s)?\b", re.IGNORECASE),
    re.compile(r"(?:for\s+)?(\d+)\s*week(?:s)?\b", re.IGNORECASE),
    re.compile(r"(?:for\s+)?(\d+)\s*month(?:s)?\b", re.IGNORECASE),
    re.compile(r"(\d+)\s*/\s*7\b"),      # 5/7 = 5 days
    re.compile(r"(\d+)\s*/\s*52\b"),     # 1/52 = 1 week
    re.compile(r"(\d+)\s*/\s*12\b"),     # 1/12 = 1 month
    re.compile(r"\b(\d{1,2})\s*d(?:ays?)?\b", re.IGNORECASE),
]

_DURATION_MULT = {
    "day": 1, "days": 1, "week": 7, "weeks": 7, "month": 30, "months": 30,
}

# Doctor / patient header patterns
_DOCTOR_RE = re.compile(
    r"(?:Dr\.?|Doctor|Physician|Consultant|Prof\.?)\s+([A-Z][A-Za-z'\-\.]+(?:\s+[A-Z][A-Za-z'\-\.]+){0,3})",
    re.IGNORECASE,
)
_PATIENT_RE = re.compile(
    r"(?:Patient|Pt\.?|Name)\s*[:\-]\s*([A-Z][A-Za-z'\-\.]+(?:\s+[A-Z][A-Za-z'\-\.]+){0,3})",
    re.IGNORECASE,
)
_DATE_RE = re.compile(
    r"\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{2,4}[-/\.]\d{1,2}[-/\.]\d{1,2})\b"
)
_HOSPITAL_RE = re.compile(
    r"(?:Hospital|Clinic|Centre|Center|Medical|Nursing|Health)\b[^,\n]{0,40}",
    re.IGNORECASE,
)

# Noise lines to skip
_SKIP_PATTERNS = [
    re.compile(r"^\s*(?:tel|ph|phone|fax|mob|email|www|http|address|reg\.?\s*no)[\s:\.]+", re.IGNORECASE),
    re.compile(r"^\s*[*#]{3,}", re.IGNORECASE),
    re.compile(r"^\s*[_\-]{4,}"),
    re.compile(r"^\s*page\s+\d", re.IGNORECASE),
]

# Dosage form prefixes to strip
_FORM_PREFIX = re.compile(
    r"^\s*(?:tab(?:let)?s?\.?|cap(?:sule)?s?\.?|inj(?:ection)?s?\.?|"
    r"syr(?:up)?\.?|susp(?:ension)?\.?|oint(?:ment)?\.?|"
    r"drop[s]?\.?|gel\.?|cream\.?|lotion\.?|spray\.?|patch\.?|"
    r"sach(?:et)?s?\.?|granules?\.?|powder\.?)\s+",
    re.IGNORECASE,
)

# Hints that a noisy line may still be a medicine entry.
_FALLBACK_HINT_RE = re.compile(
    r"\b(?:tab(?:let)?|cap(?:sule)?|inj(?:ection)?|syr(?:up)?|susp(?:ension)?|"
    r"drop|mg|mcg|ml|iu|od|bd|tds|qid|bid|tid|hs|sos|prn|am|pm)\b|"
    r"\b\d\s*[-–]\s*\d\s*[-–]\s*\d\b",
    re.IGNORECASE,
)


class PrescriptionParser:

    def __init__(self, threshold: float = 0.50) -> None:
        self._threshold = threshold
        self._corrector = MedicineCorrector()
        self._freq_parser = FrequencyParser()

    def parse(
        self,
        merged: MergedResult,
        preprocessing_variants: List[str],
        image_quality: float,
        start_time: float,
    ) -> PrescriptionResult:
        text = merged.text
        lines = text.split("\n")
        warnings: List[str] = []

        # ── Header parsing ─────────────────────────────────────────────────────
        doctor_name = self._extract_first(text, _DOCTOR_RE)
        patient_name = self._extract_first(text, _PATIENT_RE)
        date = self._extract_first(text, _DATE_RE)
        hospital = ""
        m = _HOSPITAL_RE.search(text)
        if m:
            hospital = m.group(0).strip()

        # ── Line scoring → medicine candidates ────────────────────────────────
        medicine_entries: List[MedicineEntry] = []

        for line in lines:
            stripped = line.strip()
            if len(stripped) < 4:
                continue
            if any(p.match(stripped) for p in _SKIP_PATTERNS):
                continue

            score = self._line_score(stripped)
            if score < 3:
                continue

            entry = self._parse_medicine_line(stripped, merged.avg_confidence)
            if entry:
                medicine_entries.append(entry)

        # If strict pass finds nothing, try a lenient salvage pass.
        # This keeps difficult handwritten prescriptions usable instead of empty.
        fallback_used = False
        if not medicine_entries:
            medicine_entries = self._fallback_extract_medicines(lines, merged.avg_confidence)
            fallback_used = len(medicine_entries) > 0

        # ── Warnings ───────────────────────────────────────────────────────────
        if merged.avg_confidence < self._threshold:
            warnings.append(
                f"Low OCR confidence ({merged.avg_confidence:.0%}). "
                "Results may be inaccurate — please review carefully."
            )

        if fallback_used:
            warnings.append(
                "Automatic fallback extraction was used due to weak OCR signal. "
                "Please verify medicine names before confirming reminders."
            )

        uncertain_count = sum(1 for e in medicine_entries if e.is_uncertain)
        if uncertain_count > 0:
            warnings.append(
                f"{uncertain_count} medicine(s) could not be matched to the database. "
                "Please verify the names."
            )

        if not medicine_entries:
            warnings.append("No medicines could be extracted. The image may be unclear or not a prescription.")

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return PrescriptionResult(
            medicines=medicine_entries,
            doctor_name=doctor_name,
            patient_name=patient_name,
            date=date,
            hospital=hospital,
            raw_text=text,
            warnings=warnings,
            overall_confidence=merged.avg_confidence,
            processing_metadata=ProcessingMetadata(
                ocr_engines_used=merged.engines_used,
                preprocessing_variants_tried=preprocessing_variants,
                processing_time_ms=elapsed_ms,
                image_quality_score=image_quality,
                selected_variant=merged.engines_used[0] if merged.engines_used else "unknown",
            ),
        )

    # ── Line scoring ────────────────────────────────────────────────────────────

    def _line_score(self, line: str) -> int:
        score = 0
        upper = line.upper()

        if _DOSAGE_RE.search(line):
            score += 5

        freq_codes = ["OD", "BD", "TDS", "QID", "BID", "TID", "SOS", "PRN", "HS",
                      "Q4H", "Q6H", "Q8H", "Q12H", "STAT"]
        if any(f"\b{code}\b" for code in freq_codes if re.search(rf"\b{code}\b", upper)):
            score += 3

        if re.search(r"\b\d\s*[-–]\s*\d\s*[-–]\s*\d\b", line):
            score += 4

        if re.search(r"\d+\s*(?:day|week|month)s?\b", line, re.IGNORECASE):
            score += 2

        if re.match(r"^\s*\d+[\.\)]\s+\S", line):
            score += 1  # Numbered list item

        if re.match(r"^\s*[-•*]\s+\S", line):
            score += 1  # Bulleted list

        # Penalty: looks like a header/footer
        if re.search(r"\d{10}|\bwww\b|@|address|signature", line, re.IGNORECASE):
            score -= 3

        # Short lines rarely contain full medicine entries
        if len(line.strip()) < 8:
            score -= 2

        return score

    # ── Per-line extraction ────────────────────────────────────────────────────

    def _parse_medicine_line(self, line: str, base_conf: float) -> Optional[MedicineEntry]:
        residual = line.strip()

        # Strip leading number/bullet
        residual = re.sub(r"^\d+[\.\)]\s*", "", residual).strip()
        residual = re.sub(r"^[-•*]\s*", "", residual).strip()

        # Extract dosage
        dosage_str, residual = self._extract_dosage(residual)

        # Extract frequency
        freq = self._freq_parser.parse(residual)
        # Strip found frequency text from residual
        residual = self._strip_freq_text(residual, freq.raw_match)

        # Extract duration
        duration_days, residual = self._extract_duration(residual)

        # Strip timing note text (already captured by freq parser)
        residual = self._strip_timing(residual)

        # What remains is the medicine name candidate
        name_candidate = _FORM_PREFIX.sub("", residual).strip()
        name_candidate = re.sub(r"\s{2,}", " ", name_candidate)
        name_candidate = name_candidate.strip(" ,;:-/\\")

        if not name_candidate or len(name_candidate) < 2:
            return None

        correction = self._corrector.correct(name_candidate)

        # Confidence: blend OCR confidence with fuzzy match score
        match_conf = correction.score / 100.0
        combined_conf = 0.4 * base_conf + 0.6 * match_conf

        return MedicineEntry(
            name=name_candidate,
            corrected_name=correction.corrected,
            dosage=dosage_str,
            frequency=freq.full_name,
            frequency_code=freq.code,
            times_per_day=freq.times_per_day,
            duration_days=duration_days,
            timing_notes=freq.timing_note,
            reminder_times=freq.reminder_times,
            confidence=round(combined_conf, 3),
            is_uncertain=correction.is_uncertain or combined_conf < 0.55,
        )

    def _extract_dosage(self, line: str) -> Tuple[str, str]:
        m = _DOSAGE_RE.search(line)
        if not m:
            return "", line
        dosage_str = m.group(0)
        residual = line[:m.start()] + line[m.end():]
        return dosage_str.strip(), residual.strip()

    def _extract_duration(self, line: str) -> Tuple[int, str]:
        for pat in _DURATION_PATTERNS:
            m = pat.search(line)
            if m:
                n = int(m.group(1).replace(",", ""))
                raw = m.group(0).lower()
                mult = 1
                for key, val in _DURATION_MULT.items():
                    if key in raw:
                        mult = val
                        break
                residual = line[:m.start()] + line[m.end():]
                return n * mult, residual.strip()
        return 0, line

    def _strip_freq_text(self, line: str, raw_match: str) -> str:
        if not raw_match:
            return line
        try:
            return re.sub(re.escape(raw_match), "", line, flags=re.IGNORECASE).strip()
        except Exception:
            return line

    def _strip_timing(self, line: str) -> str:
        from app.services.frequency_parser import _TIMING_PATTERNS
        for pattern, _ in _TIMING_PATTERNS:
            line = re.sub(pattern, "", line, flags=re.IGNORECASE).strip()
        return line

    def _fallback_extract_medicines(self, lines: List[str], base_conf: float) -> List[MedicineEntry]:
        """
        Lenient fallback extraction for difficult handwritten scans.

        Runs only when strict parsing returns zero medicines. It accepts weaker
        line signals but marks all recovered entries as uncertain for manual review.
        """
        recovered: List[MedicineEntry] = []
        seen: set[str] = set()

        for line in lines:
            stripped = line.strip()
            if len(stripped) < 6:
                continue
            if any(p.match(stripped) for p in _SKIP_PATTERNS):
                continue
            if _DOCTOR_RE.search(stripped) or _PATIENT_RE.search(stripped) or _HOSPITAL_RE.search(stripped):
                continue

            score = self._line_score(stripped)
            if score < 1 and not _FALLBACK_HINT_RE.search(stripped):
                continue

            entry = self._parse_medicine_line(stripped, base_conf)
            if not entry:
                continue

            key = (entry.corrected_name or entry.name).strip().lower()
            if not key or key in seen:
                continue

            entry.is_uncertain = True
            entry.confidence = min(entry.confidence, 0.45)
            if entry.times_per_day <= 0:
                entry.times_per_day = 1
            if not entry.reminder_times:
                entry.reminder_times = ["08:00"]

            recovered.append(entry)
            seen.add(key)

            # Keep output manageable; users can re-run on cropped images for more.
            if len(recovered) >= 8:
                break

        return recovered

    @staticmethod
    def _extract_first(text: str, pattern: re.Pattern) -> str:
        m = pattern.search(text)
        return m.group(1).strip() if m else ""
