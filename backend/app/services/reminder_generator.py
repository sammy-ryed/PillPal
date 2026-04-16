"""
Reminder schedule generator.

Takes a confirmed list of MedicineEntry objects and produces:
- A per-medicine schedule (start/end dates, daily times)
- A day-by-day slot list for calendar integration

Default start date: tomorrow.
Ongoing medicines (duration_days = 0) generate 30 days of reminders.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List

from app.models.prescription import MedicineEntry
from app.models.reminder import DaySchedule, MedicineSchedule, ReminderPlan, ReminderSlot
from app.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_DURATION_DAYS = 30
_DEFAULT_DAILY_TIME = "08:00"


class ReminderGenerator:

    def generate(
        self,
        medicines: List[MedicineEntry],
        prescription_id: str | None = None,
        start_date: date | None = None,
    ) -> ReminderPlan:
        if start_date is None:
            start_date = date.today() + timedelta(days=1)

        med_schedules: List[MedicineSchedule] = []

        for med in medicines:
            duration = med.duration_days if med.duration_days > 0 else _DEFAULT_DURATION_DAYS
            end = start_date + timedelta(days=duration - 1)
            times = med.reminder_times if med.reminder_times else [_DEFAULT_DAILY_TIME]

            med_schedules.append(MedicineSchedule(
                medicine_name=med.corrected_name or med.name,
                dosage=med.dosage,
                start_date=start_date.isoformat(),
                end_date=end.isoformat(),
                duration_days=duration,
                times_per_day=med.times_per_day,
                daily_times=times,
                timing_note=med.timing_notes,
                is_ongoing=(med.duration_days == 0),
            ))

        # Build full daily calendar
        if med_schedules:
            overall_end = max(
                date.fromisoformat(s.end_date) for s in med_schedules
            )
        else:
            overall_end = start_date + timedelta(days=_DEFAULT_DURATION_DAYS - 1)

        daily: List[DaySchedule] = []
        total_doses = 0
        current = start_date
        day_num = 1

        while current <= overall_end:
            slots: List[ReminderSlot] = []
            for sched in med_schedules:
                s_date = date.fromisoformat(sched.start_date)
                e_date = date.fromisoformat(sched.end_date)
                if s_date <= current <= e_date:
                    for t in sched.daily_times:
                        slots.append(ReminderSlot(
                            time=t,
                            medicine_name=sched.medicine_name,
                            dosage=sched.dosage,
                            timing_note=sched.timing_note,
                        ))
                        total_doses += 1

            slots.sort(key=lambda s: s.time)

            if slots:
                daily.append(DaySchedule(
                    date=current.isoformat(),
                    day_number=day_num,
                    slots=slots,
                ))

            current += timedelta(days=1)
            day_num += 1

        logger.info(
            f"Generated reminder plan: {len(med_schedules)} medicines, "
            f"{len(daily)} days, {total_doses} total doses."
        )

        return ReminderPlan(
            prescription_id=prescription_id,
            medicines=med_schedules,
            daily_schedule=daily,
            total_doses=total_doses,
            start_date=start_date.isoformat(),
            end_date=overall_end.isoformat(),
            calendar_events=[],  # Google Calendar hook (future)
            sms_payload=None,    # Twilio hook (future)
        )
