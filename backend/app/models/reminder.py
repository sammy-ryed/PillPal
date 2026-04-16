"""
Pydantic models for reminder schedule generation.
Structured for future Google Calendar / Twilio / WhatsApp integration.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReminderSlot(BaseModel):
    """A single dose event within a day."""

    time: str = Field(description="HH:MM 24-hour format")
    medicine_name: str
    dosage: str
    timing_note: str = ""


class DaySchedule(BaseModel):
    """All doses for a single calendar day."""

    date: str = Field(description="YYYY-MM-DD")
    day_number: int = Field(description="1-indexed day of treatment")
    slots: List[ReminderSlot]


class MedicineSchedule(BaseModel):
    """Full schedule for one medicine across its duration."""

    medicine_name: str
    dosage: str
    start_date: str
    end_date: str
    duration_days: int
    times_per_day: int
    daily_times: List[str] = Field(description="HH:MM strings")
    timing_note: str = ""
    is_ongoing: bool = False


class ReminderPlan(BaseModel):
    """
    Complete reminder plan returned after user confirms prescription.
    Designed as a hook for calendar / notification integrations.
    """

    prescription_id: Optional[str] = None
    medicines: List[MedicineSchedule]
    daily_schedule: List[DaySchedule]
    total_doses: int
    start_date: str
    end_date: str

    # Integration hooks — populated by future services
    calendar_events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Google Calendar event payloads (future)",
    )
    sms_payload: Optional[Dict[str, Any]] = Field(
        default=None, description="Twilio SMS payload (future)"
    )
