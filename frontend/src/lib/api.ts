// Backend API client — all calls go through this module.
// Change API_BASE to point to a deployed server when ready.
//
// Endpoints:
//   POST /api/prescriptions/parse          — Upload prescription image
//   POST /api/prescriptions/reminders      — Generate reminder plan
//   GET  /api/prescriptions/medicines      — List all medicines (?q=search&limit=100)
//   GET  /api/prescriptions/medicines/count — medicine count in DB
//   GET  /api/health

import type { PrescriptionResult, ReminderPlan } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function parsePrescription(
  file: File
): Promise<PrescriptionResult> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/api/prescriptions/parse`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail ?? "Parse request failed");
  }

  return res.json();
}

export async function generateReminders(
  result: PrescriptionResult
): Promise<ReminderPlan> {
  const res = await fetch(`${API_BASE}/api/prescriptions/reminders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail ?? "Reminder generation failed");
  }

  return res.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Backend offline");
  return res.json();
}

/**
 * Fetch all medicines in the database.
 * @param query Optional search string — returns medicines whose names contain it
 * @param limit Max results (default 100, max 500)
 */
export async function getMedicines(
  query?: string,
  limit = 100
): Promise<string[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (query) params.set("q", query);

  const res = await fetch(
    `${API_BASE}/api/prescriptions/medicines?${params.toString()}`
  );
  if (!res.ok) throw new Error(`Medicine fetch failed: HTTP ${res.status}`);
  return res.json();
}

/**
 * Get the number of medicines stored in the DB (useful for dashboard stats).
 */
export async function getMedicineCount(): Promise<{
  count: number;
  source: string;
}> {
  const res = await fetch(
    `${API_BASE}/api/prescriptions/medicines/count`
  );
  if (!res.ok) throw new Error(`Medicine count failed: HTTP ${res.status}`);
  return res.json();
}
