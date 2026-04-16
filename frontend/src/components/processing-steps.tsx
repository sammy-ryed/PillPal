"use client";

import React from "react";

const STEPS = [
  { id: 1, label: "Preprocessing image",       sub: "Deskew · CLAHE · denoise" },
  { id: 2, label: "Running OCR engines",        sub: "EasyOCR + Tesseract" },
  { id: 3, label: "Merging outputs",            sub: "Confidence-weighted merge" },
  { id: 4, label: "Extracting medicines",       sub: "Name · dosage · frequency" },
  { id: 5, label: "Building reminder schedule", sub: "Daily · weekly · ongoing" },
];

interface Props {
  activeStep: number; // 1-5; 6 = all done
  error?: string | null;
}

export function ProcessingSteps({ activeStep, error }: Props) {
  return (
    <div style={{ maxWidth: 520, margin: "0 auto", paddingTop: 40 }}>
      {/* Spinner */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 48 }}>
        <div
          style={{
            width: 64,
            height: 64,
            position: "relative",
          }}
        >
          <div
            className="spinner"
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "50%",
              border: "2px solid rgba(42,37,32,0.1)",
              borderTopColor: "var(--color-terra)",
            }}
          />
          <div
            className="spinner-inner"
            style={{
              position: "absolute",
              inset: 10,
              borderRadius: "50%",
              border: "2px solid rgba(42,37,32,0.06)",
              borderTopColor: "var(--color-sage)",
            }}
          />
        </div>
      </div>

      {/* Steps */}
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {STEPS.map(({ id, label, sub }) => {
          const done   = id < activeStep;
          const active = id === activeStep;

          return (
            <div
              key={id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                padding: "14px 20px",
                borderRadius: 6,
                background: active
                  ? "white"
                  : done
                  ? "rgba(122,158,142,0.05)"
                  : "transparent",
                border: active
                  ? "1px solid rgba(196,92,58,0.2)"
                  : done
                  ? "1px solid rgba(122,158,142,0.15)"
                  : "1px solid transparent",
                transition: "all 0.3s ease",
              }}
            >
              {/* Status dot */}
              <div
                className={active ? "pulse-ring" : ""}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  flexShrink: 0,
                  background: done
                    ? "var(--color-sage)"
                    : active
                    ? "var(--color-terra)"
                    : "rgba(42,37,32,0.15)",
                  transition: "background 0.3s",
                }}
              />

              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 14,
                    fontWeight: active ? 500 : 400,
                    color: done
                      ? "var(--color-sage-dark)"
                      : active
                      ? "var(--color-charcoal)"
                      : "var(--color-warm-gray)",
                    transition: "color 0.3s",
                  }}
                >
                  {label}
                </div>
                {active && (
                  <div
                    style={{
                      fontSize: 12,
                      fontFamily: "var(--font-mono)",
                      color: "var(--color-warm-gray)",
                      marginTop: 3,
                    }}
                  >
                    {sub}
                  </div>
                )}
              </div>

              {/* Check or step number */}
              <span
                style={{
                  fontSize: 12,
                  fontFamily: "var(--font-mono)",
                  color: done
                    ? "var(--color-sage)"
                    : "rgba(42,37,32,0.2)",
                }}
              >
                {done ? "done" : `0${id}`}
              </span>
            </div>
          );
        })}
      </div>

      {error && (
        <div
          style={{
            marginTop: 24,
            padding: "16px 20px",
            borderRadius: 6,
            background: "rgba(196,92,58,0.07)",
            border: "1px solid rgba(196,92,58,0.25)",
            fontSize: 14,
            color: "var(--color-terra)",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              fontWeight: 600,
              marginRight: 10,
            }}
          >
            ERROR
          </span>
          {error}
        </div>
      )}
    </div>
  );
}
