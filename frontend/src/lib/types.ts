// Shared TypeScript types for the PillPal frontend.
// Mirrors the Pydantic models in backend/app/models/

export interface MedicineEntry {
  name: string;
  corrected_name: string;
  dosage: string;
  frequency: string;
  frequency_code: string;
  times_per_day: number;
  duration_days: number;
  timing_notes: string;
  reminder_times: string[];
  confidence: number;
  is_uncertain: boolean;
}

export interface ProcessingMetadata {
  ocr_engines_used: string[];
  preprocessing_variants_tried: string[];
  processing_time_ms: number;
  image_quality_score: number;
  selected_variant: string;
}

export interface PrescriptionResult {
  id?: string;
  medicines: MedicineEntry[];
  doctor_name: string;
  patient_name: string;
  date: string;
  hospital: string;
  raw_text: string;
  warnings: string[];
  overall_confidence: number;
  processing_metadata: ProcessingMetadata;
}

export interface ReminderSlot {
  time: string;
  medicine_name: string;
  dosage: string;
  timing_note: string;
}

export interface DaySchedule {
  date: string;
  day_number: number;
  slots: ReminderSlot[];
}

export interface MedicineSchedule {
  medicine_name: string;
  dosage: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  times_per_day: number;
  daily_times: string[];
  timing_note: string;
  is_ongoing: boolean;
}

export interface ReminderPlan {
  prescription_id?: string;
  medicines: MedicineSchedule[];
  daily_schedule: DaySchedule[];
  total_doses: number;
  start_date: string;
  end_date: string;
}

export type ConfidenceLevel = "high" | "medium" | "low";
export function confidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.85) return "high";
  if (score >= 0.60) return "medium";
  return "low";
}
