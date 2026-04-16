"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { usePrescription } from "@/store/prescription-context";
import { generateReminders } from "@/lib/api";
import { MedicineCard } from "@/components/medicine-card";
import type { MedicineEntry } from "@/lib/types";

export default function ResultsPage() {
  const router = useRouter();
  const { parsedResult, setParsedResult, setReminderPlan, uploadedFile } =
    usePrescription();

  const [meds, setMeds] = useState<MedicineEntry[]>(
    parsedResult?.medicines ?? []
  );
  const [confirming, setConfirming] = useState(false);
  const [error, setError]         = useState<string | null>(null);

  if (!parsedResult) {
    return (
      <EmptyState
        message="No prescription loaded."
        action={{ label: "Upload one", href: "/upload" }}
      />
    );
  }

  const conf = parsedResult.overall_confidence;

  const handleUpdateMed = (index: number, updated: MedicineEntry) => {
    const next = [...meds];
    next[index] = updated;
    setMeds(next);
  };

  const handleConfirm = async () => {
    setConfirming(true);
    setError(null);
    try {
      const payload = { ...parsedResult, medicines: meds };
      const plan    = await generateReminders(payload);
      setParsedResult(payload);
      setReminderPlan(plan);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to generate reminders");
      setConfirming(false);
    }
  };

  const totalDoses = meds.reduce((acc, m) => acc + (m.times_per_day || 1), 0);

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
        display: "grid",
        gridTemplateColumns: "1fr 340px",
        gap: 32,
        alignItems: "start",
      }}
    >
      {/* Left: medicine cards */}
      <div>
        <div style={{ marginBottom: 32 }}>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              color: "var(--color-warm-gray)",
              marginBottom: 8,
            }}
          >
            Extracted Results
          </div>
          <h1
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "clamp(28px, 3vw, 40px)",
              fontWeight: 400,
              marginBottom: 6,
            }}
          >
            {meds.length} {meds.length === 1 ? "medicine" : "medicines"} found
          </h1>
          <p style={{ fontSize: 14, color: "var(--color-warm-gray)" }}>
            OCR confidence {Math.round(conf * 100)}% — edit any field to correct
          </p>
        </div>

        {/* Warnings */}
        {parsedResult.warnings.map((w, i) => (
          <div
            key={i}
            style={{
              background: "rgba(196,92,58,0.06)",
              border: "1px solid rgba(196,92,58,0.2)",
              borderRadius: 6,
              padding: "12px 16px",
              fontSize: 13,
              color: "var(--color-terra)",
              marginBottom: 12,
              display: "flex",
              gap: 10,
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                fontWeight: 600,
                flexShrink: 0,
                paddingTop: 2,
              }}
            >
              WARN
            </span>
            {w}
          </div>
        ))}

        {/* Cards */}
        {meds.length === 0 ? (
          <div
            style={{
              padding: "48px 24px",
              textAlign: "center",
              color: "var(--color-warm-gray)",
              fontSize: 14,
              background: "white",
              borderRadius: 8,
              border: "1px solid rgba(42,37,32,0.08)",
            }}
          >
            No medicines detected. Try re-uploading with a clearer image.
          </div>
        ) : (
          meds.map((med, i) => (
            <MedicineCard
              key={i}
              medicine={med}
              index={i}
              onChange={(updated) => handleUpdateMed(i, updated)}
            />
          ))
        )}
      </div>

      {/* Right: metadata + confirm */}
      <div style={{ position: "sticky", top: 100 }}>
        {/* Scan preview + metadata */}
        <div
          style={{
            background: "white",
            border: "1px solid rgba(42,37,32,0.1)",
            borderRadius: 8,
            marginBottom: 16,
            overflow: "hidden",
          }}
        >
          {/* Image area */}
          <div
            style={{
              height: 180,
              background: "var(--color-parchment)",
              position: "relative",
              overflow: "hidden",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <ScanLine />
            {uploadedFile ? (
              <UploadedPreview file={uploadedFile} />
            ) : (
              <DocIcon />
            )}
          </div>

          {/* Metadata */}
          <div style={{ padding: "20px 24px" }}>
            <div
              style={{
                fontSize: 12,
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 16,
                color: "var(--color-charcoal)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              Prescription scan
              <span
                style={{
                  fontSize: 10,
                  fontFamily: "var(--font-mono)",
                  padding: "3px 10px",
                  borderRadius: 20,
                  background:
                    conf >= 0.75
                      ? "rgba(122,158,142,0.15)"
                      : "rgba(196,92,58,0.1)",
                  color:
                    conf >= 0.75 ? "var(--color-sage-dark)" : "var(--color-terra)",
                }}
              >
                {Math.round(conf * 100)}% confident
              </span>
            </div>
            {[
              ["Doctor",  parsedResult.doctor_name  || "Not detected"],
              ["Date",    parsedResult.date          || "Not detected"],
              ["Hospital",parsedResult.hospital      || "Not detected"],
              ["Medicines",`${meds.length} found`],
              ["Quality", conf >= 0.75 ? "High" : conf >= 0.5 ? "Medium" : "Low"],
            ].map(([label, value]) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  paddingBottom: 10,
                  marginBottom: 10,
                  borderBottom: "1px solid rgba(42,37,32,0.06)",
                  fontSize: 13,
                }}
              >
                <span style={{ color: "var(--color-warm-gray)" }}>{label}</span>
                <span style={{ fontWeight: 500, textAlign: "right", maxWidth: 160, fontSize: 12 }}>
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Confirm bar */}
        <div
          style={{
            background: "var(--color-charcoal)",
            borderRadius: 8,
            padding: 24,
          }}
        >
          <div
            style={{
              color: "var(--color-cream)",
              fontSize: 16,
              fontWeight: 500,
              marginBottom: 6,
            }}
          >
            Everything looks right?
          </div>
          <div
            style={{
              color: "rgba(247,243,238,0.5)",
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              marginBottom: 20,
            }}
          >
            {meds.length} medicines · {totalDoses} daily doses · starting tomorrow
          </div>

          {error && (
            <div
              style={{
                background: "rgba(196,92,58,0.2)",
                border: "1px solid rgba(196,92,58,0.3)",
                borderRadius: 4,
                padding: "10px 14px",
                fontSize: 12,
                color: "#E8967C",
                marginBottom: 16,
              }}
            >
              {error}
            </div>
          )}

          <button
            onClick={handleConfirm}
            disabled={confirming}
            style={{
              width: "100%",
              background: confirming ? "rgba(247,243,238,0.2)" : "var(--color-terra)",
              color: "var(--color-cream)",
              border: "none",
              padding: "14px",
              borderRadius: 4,
              fontSize: 15,
              fontWeight: 500,
              cursor: confirming ? "not-allowed" : "pointer",
              transition: "background 0.2s",
            }}
          >
            {confirming ? "Generating schedule..." : "Confirm & Set Reminders"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ScanLine() {
  return (
    <div
      className="scan-line"
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        height: 1,
        background: "rgba(196,92,58,0.5)",
        zIndex: 2,
      }}
    />
  );
}

function UploadedPreview({ file }: { file: File }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const reader = new FileReader();

    reader.onload = (e) => {
      if (isMounted) {
        setSrc(e.target?.result as string);
      }
    };

    reader.readAsDataURL(file);

    return () => {
      isMounted = false;
      reader.onload = null;
      if (reader.readyState === FileReader.LOADING) {
        reader.abort();
      }
    };
  }, [file]);

  return src ? (
    <img src={src} alt="Prescription" style={{ width: "100%", height: "100%", objectFit: "contain", padding: 8 }} />
  ) : (
    <DocIcon />
  );
}

function DocIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-warm-gray)" strokeWidth="1">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  );
}

function EmptyState({
  message,
  action,
}: {
  message: string;
  action: { label: string; href: string };
}) {
  return (
    <div
      style={{
        paddingTop: 180,
        textAlign: "center",
        color: "var(--color-warm-gray)",
      }}
    >
      <p style={{ marginBottom: 20, fontSize: 15 }}>{message}</p>
      <a
        href={action.href}
        style={{
          color: "var(--color-terra)",
          textDecoration: "none",
          fontSize: 14,
          borderBottom: "1px solid var(--color-terra)",
          paddingBottom: 1,
        }}
      >
        {action.label}
      </a>
    </div>
  );
}
