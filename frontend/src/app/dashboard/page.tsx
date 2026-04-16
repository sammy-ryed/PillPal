"use client";

import { useState } from "react";
import Link from "next/link";
import { usePrescription } from "@/store/prescription-context";
import type { ReminderSlot } from "@/lib/types";

const CARD_COLORS = ["#C45C3A","#7A9E8E","#4A7060","#E8967C","#B8D4C8","#8A837A"];

export default function DashboardPage() {
  const { reminderPlan, parsedResult } = usePrescription();

  const today = new Date();
  const dayLabel = today.toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  const hour = today.getHours();
  const greeting =
    hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  const todaySlots: ReminderSlot[] =
    reminderPlan?.daily_schedule?.[0]?.slots ?? [];
  const meds = parsedResult?.medicines ?? [];

  const [takenSet, setTakenSet] = useState<Set<number>>(new Set());

  const markTaken = (idx: number) =>
    setTakenSet((prev) => new Set([...prev, idx]));

  const takenCount = takenSet.size;

  return (
    <div
      className="page-enter"
      style={{
        paddingTop: 120,
        paddingBottom: 80,
        maxWidth: 1200,
        margin: "0 auto",
        paddingLeft: "clamp(16px, 4vw, 60px)",
        paddingRight: "clamp(16px, 4vw, 60px)",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          marginBottom: 40,
          flexWrap: "wrap",
          gap: 16,
        }}
      >
        <div>
          <div style={{ color: "var(--color-warm-gray)", fontSize: 14, marginBottom: 4 }}>
            {greeting}
          </div>
          <h1
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "clamp(28px, 3.5vw, 44px)",
              fontWeight: 400,
            }}
          >
            {parsedResult?.patient_name
              ? `${parsedResult.patient_name}'s medicines`
              : "Today's medicines"}
          </h1>
        </div>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 13,
            color: "var(--color-warm-gray)",
            border: "1px solid rgba(42,37,32,0.12)",
            padding: "8px 16px",
            borderRadius: 4,
          }}
        >
          {dayLabel}
        </div>
      </div>

      {/* Stats row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 16,
          marginBottom: 32,
        }}
      >
        {[
          {
            label: "Taken today",
            value: `${takenCount}/${todaySlots.length}`,
            sub: todaySlots.length === 0 ? "No reminders set" : `${todaySlots.length - takenCount} remaining`,
            color: "var(--color-sage)",
          },
          {
            label: "Active medicines",
            value: meds.length,
            sub: "From last prescription",
            color: "var(--color-terra)",
          },
          {
            label: "Total doses",
            value: reminderPlan?.total_doses ?? "—",
            sub: "In this course",
            color: "var(--color-sage-dark)",
          },
        ].map(({ label, value, sub, color }) => (
          <div
            key={label}
            style={{
              background: "white",
              border: "1px solid rgba(42,37,32,0.08)",
              borderRadius: 8,
              padding: "24px 28px",
            }}
          >
            <div style={{ fontSize: 12, color: "var(--color-warm-gray)", marginBottom: 10 }}>
              {label}
            </div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: 36,
                color,
                marginBottom: 4,
              }}
            >
              {value}
            </div>
            <div style={{ fontSize: 12, color: "var(--color-warm-gray)", fontFamily: "var(--font-mono)" }}>
              {sub}
            </div>
          </div>
        ))}
      </div>

      {/* Main content */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 300px",
          gap: 24,
          alignItems: "start",
        }}
      >
        {/* Today's reminders */}
        <div
          style={{
            background: "white",
            border: "1px solid rgba(42,37,32,0.08)",
            borderRadius: 8,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "20px 28px",
              borderBottom: "1px solid rgba(42,37,32,0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span style={{ fontWeight: 500, fontSize: 15 }}>
              Today&apos;s reminders
            </span>
            <span
              style={{
                fontSize: 11,
                fontFamily: "var(--font-mono)",
                color: "var(--color-warm-gray)",
              }}
            >
              {todaySlots.length} doses
            </span>
          </div>

          {todaySlots.length === 0 ? (
            <EmptyReminders />
          ) : (
            todaySlots.map((slot, i) => (
              <ReminderRow
                key={i}
                slot={slot}
                taken={takenSet.has(i)}
                onTake={() => markTaken(i)}
              />
            ))
          )}
        </div>

        {/* Active medicines list */}
        <div
          style={{
            background: "white",
            border: "1px solid rgba(42,37,32,0.08)",
            borderRadius: 8,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "20px 24px",
              borderBottom: "1px solid rgba(42,37,32,0.08)",
              fontWeight: 500,
              fontSize: 15,
            }}
          >
            Active medicines
          </div>
          {meds.length === 0 ? (
            <div
              style={{
                padding: 24,
                textAlign: "center",
                fontSize: 13,
                color: "var(--color-warm-gray)",
              }}
            >
              No prescription loaded.{" "}
              <Link href="/upload" style={{ color: "var(--color-terra)", textDecoration: "none" }}>
                Upload one
              </Link>
            </div>
          ) : (
            meds.map((med, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  padding: "14px 24px",
                  borderBottom:
                    i < meds.length - 1 ? "1px solid rgba(42,37,32,0.06)" : "none",
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: CARD_COLORS[i % CARD_COLORS.length],
                    flexShrink: 0,
                  }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {med.corrected_name || med.name}
                    {med.dosage && (
                      <span style={{ color: "var(--color-warm-gray)", fontWeight: 400, marginLeft: 4 }}>
                        {med.dosage}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--color-warm-gray)", marginTop: 2 }}>
                    {med.frequency || med.frequency_code}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Upload another */}
      {meds.length > 0 && (
        <div style={{ marginTop: 32, textAlign: "center" }}>
          <Link
            href="/upload"
            style={{
              fontSize: 14,
              color: "var(--color-warm-gray)",
              textDecoration: "none",
              borderBottom: "1px solid rgba(138,131,122,0.3)",
              paddingBottom: 1,
            }}
          >
            Upload another prescription
          </Link>
        </div>
      )}
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ReminderRow({
  slot,
  taken,
  onTake,
}: {
  slot: ReminderSlot;
  taken: boolean;
  onTake: () => void;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        padding: "16px 28px",
        borderBottom: "1px solid rgba(42,37,32,0.06)",
        background: taken ? "rgba(122,158,142,0.04)" : "transparent",
        transition: "background 0.3s",
      }}
    >
      {/* Time */}
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 13,
          color: taken ? "var(--color-warm-gray)" : "var(--color-charcoal)",
          minWidth: 52,
          flexShrink: 0,
        }}
      >
        {slot.time}
      </div>

      {/* Info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 500,
            color: taken ? "var(--color-warm-gray)" : "var(--color-charcoal)",
            textDecoration: taken ? "line-through" : "none",
            transition: "all 0.3s",
          }}
        >
          {slot.medicine_name}
        </div>
        <div style={{ fontSize: 12, color: "var(--color-warm-gray)", marginTop: 2 }}>
          {slot.dosage}
          {slot.timing_note ? ` · ${slot.timing_note}` : ""}
        </div>
      </div>

      {/* Status dot */}
      <div
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: taken ? "var(--color-sage)" : "rgba(196,92,58,0.4)",
          transition: "background 0.3s",
          flexShrink: 0,
        }}
      />

      {/* Mark taken */}
      <button
        onClick={onTake}
        disabled={taken}
        style={{
          background: taken ? "var(--color-sage)" : "transparent",
          color: taken ? "white" : "var(--color-charcoal)",
          border: taken ? "none" : "1px solid rgba(42,37,32,0.2)",
          padding: "7px 16px",
          borderRadius: 4,
          fontSize: 12,
          fontWeight: 500,
          cursor: taken ? "default" : "pointer",
          flexShrink: 0,
          transition: "all 0.3s",
        }}
      >
        {taken ? "Taken" : "Mark Taken"}
      </button>
    </div>
  );
}

function EmptyReminders() {
  return (
    <div
      style={{
        padding: "48px 28px",
        textAlign: "center",
        color: "var(--color-warm-gray)",
        fontSize: 14,
        lineHeight: 1.6,
      }}
    >
      No reminders for today.
      <br />
      <Link href="/upload" style={{ color: "var(--color-terra)", textDecoration: "none" }}>
        Upload a prescription
      </Link>{" "}
      to get started.
    </div>
  );
}
