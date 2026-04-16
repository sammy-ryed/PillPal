"use client";

import { useState } from "react";
import type { MedicineEntry } from "@/lib/types";
import { ConfidenceBadge } from "./confidence-badge";

const COLORS = ["#C45C3A", "#7A9E8E", "#4A7060", "#E8967C", "#B8D4C8", "#8A837A"];

interface Props {
  medicine: MedicineEntry;
  index: number;
  onChange: (updated: MedicineEntry) => void;
}

export function MedicineCard({ medicine, index, onChange }: Props) {
  const color = COLORS[index % COLORS.length];
  const [times, setTimes] = useState<string[]>(medicine.reminder_times ?? []);

  const update = (patch: Partial<MedicineEntry>) => {
    onChange({ ...medicine, ...patch });
  };

  const removeTime = (i: number) => {
    const next = times.filter((_, idx) => idx !== i);
    setTimes(next);
    update({ reminder_times: next });
  };

  const addTime = () => {
    const input = window.prompt("Add reminder time (24-hour, e.g. 14:00):");
    if (!input || !/^\d{1,2}:\d{2}$/.test(input)) return;
    const next = [...times, input];
    setTimes(next);
    update({ reminder_times: next });
  };

  return (
    <div
      style={{
        background: "white",
        border: "1px solid rgba(42,37,32,0.1)",
        borderRadius: 8,
        marginBottom: 16,
        overflow: "hidden",
        transition: "border-color 0.2s, box-shadow 0.2s",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "20px 24px",
          display: "flex",
          alignItems: "center",
          gap: 14,
          borderBottom: "1px solid rgba(42,37,32,0.08)",
        }}
      >
        <div
          style={{
            width: 4,
            alignSelf: "stretch",
            borderRadius: 4,
            background: color,
            flexShrink: 0,
          }}
        />
        <span
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 17,
            flex: 1,
            fontWeight: 400,
          }}
        >
          {medicine.corrected_name || medicine.name}
        </span>
        {medicine.is_uncertain && (
          <span
            style={{
              fontSize: 10,
              fontFamily: "var(--font-mono)",
              color: "var(--color-warm-gray)",
              background: "rgba(138,131,122,0.1)",
              padding: "2px 8px",
              borderRadius: 20,
              marginLeft: "auto",
            }}
          >
            Review
          </span>
        )}
        <ConfidenceBadge score={medicine.confidence} />
      </div>

      {/* Editable fields */}
      <div
        style={{
          padding: "20px 24px",
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 16,
        }}
      >
        <Field
          label="Medicine Name"
          value={medicine.corrected_name || medicine.name}
          onChange={(v) => update({ corrected_name: v })}
        />
        <Field
          label="Strength"
          value={medicine.dosage}
          onChange={(v) => update({ dosage: v })}
        />
        <Field
          label="Duration"
          value={medicine.duration_days > 0 ? `${medicine.duration_days} days` : "Ongoing"}
          onChange={(v) => update({ duration_days: parseInt(v) || 0 })}
        />
        <Field
          label="Frequency"
          value={medicine.frequency || medicine.frequency_code}
          onChange={(v) => update({ frequency: v })}
        />
        <Field
          label="Times / Day"
          value={String(medicine.times_per_day)}
          type="number"
          onChange={(v) => update({ times_per_day: parseInt(v) || 1 })}
        />
        <Field
          label="Timing Notes"
          value={medicine.timing_notes}
          onChange={(v) => update({ timing_notes: v })}
        />
      </div>

      {/* Time chips */}
      <div
        style={{
          padding: "14px 24px",
          borderTop: "1px solid rgba(42,37,32,0.06)",
          background: "var(--color-parchment)",
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
          alignItems: "center",
        }}
      >
        {times.map((t, i) => (
          <span
            key={i}
            style={{
              background: "white",
              border: "1px solid rgba(42,37,32,0.12)",
              padding: "5px 12px",
              borderRadius: 20,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            {t}
            <button
              onClick={() => removeTime(i)}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "var(--color-warm-gray)",
                fontSize: 15,
                lineHeight: 1,
                padding: 0,
              }}
            >
              &times;
            </button>
          </span>
        ))}
        <button
          onClick={addTime}
          style={{
            background: "transparent",
            border: "1px dashed rgba(42,37,32,0.2)",
            padding: "5px 12px",
            borderRadius: 20,
            fontSize: 12,
            color: "var(--color-warm-gray)",
            cursor: "pointer",
            fontFamily: "var(--font-sans)",
            transition: "border-color 0.2s, color 0.2s",
          }}
        >
          + Add time
        </button>
        {medicine.timing_notes && (
          <span
            style={{
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              padding: "4px 10px",
              borderRadius: 20,
              fontWeight: 500,
              background: medicine.timing_notes.toLowerCase().includes("before")
                ? "rgba(196,92,58,0.1)"
                : "var(--color-parchment)",
              color: medicine.timing_notes.toLowerCase().includes("before")
                ? "var(--color-terra)"
                : "var(--color-warm-gray)",
              border: "1px solid rgba(42,37,32,0.08)",
            }}
          >
            {medicine.timing_notes}
          </span>
        )}
      </div>
    </div>
  );
}

// ── Field sub-component ──────────────────────────────────────────────────────

interface FieldProps {
  label: string;
  value: string;
  type?: string;
  onChange: (value: string) => void;
}

function Field({ label, value, type = "text", onChange }: FieldProps) {
  return (
    <div>
      <label
        style={{
          fontSize: 10,
          textTransform: "uppercase",
          letterSpacing: "0.1em",
          color: "var(--color-warm-gray)",
          fontWeight: 500,
          marginBottom: 6,
          display: "block",
        }}
      >
        {label}
      </label>
      <input
        type={type}
        defaultValue={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: "100%",
          border: "1px solid rgba(42,37,32,0.12)",
          background: "var(--color-cream)",
          borderRadius: 4,
          padding: "8px 12px",
          fontFamily: "var(--font-sans)",
          fontSize: 14,
          color: "var(--color-charcoal)",
          outline: "none",
          transition: "border-color 0.2s, background 0.2s",
        }}
        onFocus={(e) => {
          e.target.style.borderColor = "var(--color-terra)";
          e.target.style.background = "white";
        }}
        onBlur={(e) => {
          e.target.style.borderColor = "rgba(42,37,32,0.12)";
          e.target.style.background = "var(--color-cream)";
        }}
      />
    </div>
  );
}
