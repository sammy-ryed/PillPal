"""
Frequency parser.

Converts prescription frequency notations to structured data:
- Medical abbreviations: OD, BD, TDS, QID, HS, SOS, PRN, Q8H…
- Indian notation: 1-0-1, 1-1-1, 0-0-1 (morning-afternoon-night)
- Natural language: "once daily", "before sleep", "after food"

Initialised once at startup with codes from Supabase (or fallback map).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.supabase_service import SupabaseService

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Timing note patterns (applied after frequency is resolved) ─────────────────
_TIMING_PATTERNS: List[tuple] = [
    (r"before\s+break\s*fast",       "Before breakfast"),
    (r"after\s+break\s*fast|with\s+break\s*fast", "After breakfast"),
    (r"before\s+lunch",              "Before lunch"),
    (r"after\s+lunch|with\s+lunch",  "After lunch"),
    (r"before\s+dinner",             "Before dinner"),
    (r"after\s+dinner|with\s+dinner", "After dinner"),
    (r"before\s+food|ac\b|empty\s+stomach", "Before food"),
    (r"after\s+food|pc\b|with\s+meal|with\s+food", "After food"),
    (r"at\s+bed\s*time|before\s+sleep|hs\b",       "Before sleep"),
    (r"with\s+water",                "With water"),
    (r"on\s+empty\s+stomach",        "Empty stomach"),
    (r"sublingually?",               "Under tongue"),
    (r"after\s+meal",                "After meal"),
]

# ── Natural language → frequency code mapping ──────────────────────────────────
_NL_TO_CODE: List[tuple] = [
    (r"\bonce\s+(?:a\s+)?(?:day|daily)\b|\bod\b|\bqd\b|\bdaily\b(?!\s+twice|\s+thrice|\s+four)", "OD"),
    (r"\btwice\s+(?:a\s+)?day\b|\bbd\b|\bbid\b|\btwo\s+times\b|\b2\s*times\b", "BD"),
    (r"\bthree\s+times\b|\bthrice\b|\btds\b|\btid\b|\b3\s*times\b", "TDS"),
    (r"\bfour\s+times\b|\bqid\b|\b4\s*times\b",                     "QID"),
    (r"\bat\s+bed\s*time\b|\bbedtime\b",                             "HS"),
    (r"\bas\s+needed\b|\bwhen\s+req(?:uired)?\b|\bsos\b|\bprn\b",   "SOS"),
    (r"\bq4h\b|\bevery\s+4\s+hours?\b",                              "Q4H"),
    (r"\bq6h\b|\bevery\s+6\s+hours?\b",                              "Q6H"),
    (r"\bq8h\b|\bevery\s+8\s+hours?\b",                              "Q8H"),
    (r"\bq12h\b|\bevery\s+12\s+hours?\b",                            "Q12H"),
    (r"\bweekly\b|\bonce\s+(?:a\s+)?week\b",                         "WEEKLY"),
    (r"\bmorning\s+only\b|\bevery\s+morning\b",                      "AM"),
    (r"\bevening\s+only\b|\bevery\s+evening\b",                      "PM"),
    (r"\bonce\b",                                                     "OD"),
]

# Indian notation pattern: digits like 1-0-1 or 1-1-0
_INDIAN_NOTATION = re.compile(r"\b(\d)\s*[-–]\s*(\d)\s*[-–]\s*(\d)\b")


@dataclass
class ParsedFrequency:
    code: str                  # OD, BD, TDS, etc. or INDIAN:1-0-1
    full_name: str
    times_per_day: int
    reminder_times: List[str]  # HH:MM strings
    timing_note: str
    raw_match: str


class FrequencyParser:
    """
    Singleton-style: call FrequencyParser.initialize() at startup,
    then build instances normally.
    """

    _codes: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def initialize(cls, svc: "SupabaseService") -> None:
        cls._codes = svc.get_frequency_codes()
        logger.info(f"FrequencyParser loaded {len(cls._codes)} frequency codes.")

    def parse(self, text: str) -> ParsedFrequency:
        """
        Parse frequency notation from a medicine line.
        Priority: Indian notation > abbreviation > natural language.
        """
        clean = text.strip().lower()

        # 1. Indian notation (1-0-1)
        result = self._parse_indian_notation(text)
        if result:
            result.timing_note = self._extract_timing(clean) or result.timing_note
            return result

        # 2. Medical abbreviation (OD, BD, TDS, etc.)
        result = self._parse_abbreviation(text.upper())
        if result:
            result.timing_note = self._extract_timing(clean) or result.timing_note
            return result

        # 3. Natural language
        result = self._parse_natural_language(clean)
        if result:
            result.timing_note = self._extract_timing(clean) or result.timing_note
            return result

        # 4. Default: assume once daily
        return ParsedFrequency(
            code="OD",
            full_name="Once Daily (assumed)",
            times_per_day=1,
            reminder_times=self._times_for_code("OD"),
            timing_note=self._extract_timing(clean) or "",
            raw_match="",
        )

    def _parse_indian_notation(self, text: str) -> Optional[ParsedFrequency]:
        m = _INDIAN_NOTATION.search(text)
        if not m:
            return None

        morning, afternoon, night = int(m.group(1)), int(m.group(2)), int(m.group(3))
        total = morning + afternoon + night

        times: List[str] = []
        if morning:
            times.append("08:00")
        if afternoon:
            times.append("13:00")
        if night:
            times.append("20:00")

        pattern = f"{morning}-{afternoon}-{night}"
        return ParsedFrequency(
            code=f"INDIAN:{pattern}",
            full_name=f"{total}x daily ({pattern})",
            times_per_day=total,
            reminder_times=times,
            timing_note="",
            raw_match=m.group(0),
        )

    def _parse_abbreviation(self, text: str) -> Optional[ParsedFrequency]:
        for code, data in self._codes.items():
            # Whole-word match to avoid "BD" in "ABDOMEN"
            if re.search(rf"\b{re.escape(code)}\b", text):
                return ParsedFrequency(
                    code=code,
                    full_name=data["full_name"],
                    times_per_day=data["times_per_day"],
                    reminder_times=list(data.get("default_times") or []),
                    timing_note="",
                    raw_match=code,
                )
        return None

    def _parse_natural_language(self, text: str) -> Optional[ParsedFrequency]:
        for pattern, code in _NL_TO_CODE:
            if re.search(pattern, text, re.IGNORECASE):
                data = self._codes.get(code, {})
                return ParsedFrequency(
                    code=code,
                    full_name=data.get("full_name", code),
                    times_per_day=data.get("times_per_day", 1),
                    reminder_times=list(data.get("default_times") or ["08:00"]),
                    timing_note="",
                    raw_match=pattern,
                )
        return None

    def _times_for_code(self, code: str) -> List[str]:
        data = self._codes.get(code, {})
        return list(data.get("default_times") or ["08:00"])

    @staticmethod
    def _extract_timing(text: str) -> str:
        for pattern, label in _TIMING_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return ""
