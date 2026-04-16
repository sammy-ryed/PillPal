"""
Pydantic models for prescription parsing output.
These are the canonical data structures flowing through the pipeline.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MedicineEntry(BaseModel):
    """Represents a single extracted medicine from a prescription."""

    name: str = Field(description="Raw OCR name before correction")
    corrected_name: str = Field(description="Fuzzy-matched name from medicine DB")
    dosage: str = Field(default="", description="e.g. 500mg, 40mg")
    frequency: str = Field(default="", description="Human-readable frequency")
    frequency_code: str = Field(default="", description="OD / BD / TDS / QID / etc.")
    times_per_day: int = Field(default=1, ge=0)
    duration_days: int = Field(default=0, ge=0, description="0 = ongoing / unknown")
    timing_notes: str = Field(default="", description="Before food, after meals, etc.")
    reminder_times: List[str] = Field(default_factory=list, description="HH:MM strings")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    is_uncertain: bool = Field(default=False)


class ProcessingMetadata(BaseModel):
    """Metadata about how the prescription was processed."""

    ocr_engines_used: List[str]
    preprocessing_variants_tried: List[str]
    processing_time_ms: float
    image_quality_score: float = Field(ge=0.0, le=1.0)
    selected_variant: str


class PrescriptionResult(BaseModel):
    """Full structured output from the prescription pipeline."""

    id: Optional[str] = None
    medicines: List[MedicineEntry]
    doctor_name: str = ""
    patient_name: str = ""
    date: str = ""
    hospital: str = ""
    raw_text: str
    warnings: List[str] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    processing_metadata: ProcessingMetadata
    created_at: Optional[datetime] = None
