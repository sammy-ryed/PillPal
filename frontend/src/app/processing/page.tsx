"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ProcessingSteps } from "@/components/processing-steps";
import { usePrescription } from "@/store/prescription-context";

export default function ProcessingPage() {
  const router = useRouter();
  const { parsedResult } = usePrescription();
  const [step, setStep] = useState(1);

  // Step animation — auto-advances every 600ms up to step 4.
  // Step 5 only completes when parsedResult arrives.
  useEffect(() => {
    if (step < 4) {
      const t = setTimeout(() => setStep((s) => s + 1), 700);
      return () => clearTimeout(t);
    }
    if (step === 4) {
      const t = setTimeout(() => setStep(5), 700);
      return () => clearTimeout(t);
    }
  }, [step]);

  // When result arrives, complete animation then navigate
  useEffect(() => {
    if (parsedResult && step >= 5) {
      const t = setTimeout(() => router.push("/results"), 500);
      return () => clearTimeout(t);
    }
  }, [parsedResult, step, router]);

  // Redirect to upload if there's nothing to process
  useEffect(() => {
    const t = setTimeout(() => {
      if (!parsedResult) {
        // If after 15s still no result, the fetch probably errored in upload page
      }
    }, 15_000);
    return () => clearTimeout(t);
  }, [parsedResult]);

  return (
    <div
      className="page-enter"
      style={{
        minHeight: "100vh",
        paddingTop: 120,
        paddingBottom: 80,
        paddingLeft: "clamp(20px, 5vw, 80px)",
        paddingRight: "clamp(20px, 5vw, 80px)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          textTransform: "uppercase",
          letterSpacing: "0.12em",
          color: "var(--color-warm-gray)",
          marginBottom: 12,
          textAlign: "center",
        }}
      >
        Processing
      </div>
      <h1
        style={{
          fontFamily: "var(--font-serif)",
          fontSize: "clamp(28px, 3vw, 42px)",
          fontWeight: 400,
          marginBottom: 8,
          textAlign: "center",
        }}
      >
        Reading your prescription
      </h1>
      <p
        style={{
          color: "var(--color-warm-gray)",
          fontSize: 15,
          marginBottom: 48,
          textAlign: "center",
        }}
      >
        Dual OCR engines running. Usually takes 3–8 seconds.
      </p>

      <div style={{ width: "100%", maxWidth: 520 }}>
        <ProcessingSteps activeStep={step} />
      </div>
    </div>
  );
}
