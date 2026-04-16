"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { UploadZone } from "@/components/upload-zone";
import { usePrescription } from "@/store/prescription-context";
import { parsePrescription } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const { uploadedFile, setUploadedFile, setParsedResult } = usePrescription();

  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback((file: File) => {
    setUploadedFile(file);
    setFileName(file.name);
    setFileSize((file.size / 1024 / 1024).toFixed(1) + " MB");
    setError(null);

    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(file);
    } else {
      setPreview(null);
    }
  }, [setUploadedFile]);

  const handleExtract = async () => {
    if (!uploadedFile) return;

    setLoading(true);
    setError(null);

    try {
      router.push("/processing");
      const result = await parsePrescription(uploadedFile);
      setParsedResult(result);
      router.push("/results");
    } catch (err: unknown) {
      router.push("/upload");
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
      setLoading(false);
    }
  };

  return (
    <PageShell>
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          textTransform: "uppercase",
          letterSpacing: "0.12em",
          color: "var(--color-warm-gray)",
          marginBottom: 12,
        }}
      >
        Upload Prescription
      </div>
      <h1
        style={{
          fontFamily: "var(--font-serif)",
          fontSize: "clamp(32px, 4vw, 48px)",
          fontWeight: 400,
          marginBottom: 10,
        }}
      >
        Start with a photo
      </h1>
      <p
        style={{
          color: "var(--color-warm-gray)",
          fontSize: 15,
          marginBottom: 40,
          maxWidth: 480,
        }}
      >
        Take or upload a picture of your prescription. Printed or handwritten.
      </p>

      <UploadZone onFile={handleFile} />

      {/* Preview row */}
      {fileName && (
        <div
          style={{
            marginTop: 20,
            background: "white",
            border: "1px solid rgba(42,37,32,0.1)",
            borderRadius: 8,
            padding: "20px 24px",
            display: "flex",
            alignItems: "center",
            gap: 20,
          }}
        >
          {/* Thumbnail */}
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: 6,
              background: "var(--color-parchment)",
              overflow: "hidden",
              flexShrink: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {preview ? (
              <img
                src={preview}
                alt="Preview"
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            ) : (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-warm-gray)" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            )}
          </div>

          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500, fontSize: 14 }}>{fileName}</div>
            <div style={{ fontSize: 12, color: "var(--color-warm-gray)", marginTop: 3 }}>
              {fileSize} · Ready to process
            </div>
          </div>

          <ExtractButton onClick={handleExtract} loading={loading} />
        </div>
      )}

      {error && (
        <div
          style={{
            marginTop: 16,
            background: "rgba(196,92,58,0.07)",
            border: "1px solid rgba(196,92,58,0.25)",
            borderRadius: 6,
            padding: "16px 20px",
            fontSize: 14,
            color: "var(--color-terra)",
            display: "flex",
            gap: 12,
            alignItems: "flex-start",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              fontWeight: 600,
              flexShrink: 0,
              paddingTop: 3,
            }}
          >
            ERROR
          </span>
          <div>
            <div style={{ fontWeight: 500, marginBottom: 3 }}>
              Could not process prescription
            </div>
            <div style={{ color: "var(--color-warm-gray)", fontSize: 13 }}>{error}</div>
          </div>
        </div>
      )}
    </PageShell>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="page-enter"
      style={{
        paddingTop: 120,
        paddingBottom: 80,
        paddingLeft: "clamp(20px, 5vw, 80px)",
        paddingRight: "clamp(20px, 5vw, 80px)",
        maxWidth: 820,
        margin: "0 auto",
      }}
    >
      {children}
    </div>
  );
}

function ExtractButton({
  onClick,
  loading,
}: {
  onClick: () => void;
  loading: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        background: loading ? "var(--color-warm-gray)" : "var(--color-charcoal)",
        color: "var(--color-cream)",
        border: "none",
        padding: "12px 24px",
        borderRadius: 4,
        fontSize: 14,
        fontWeight: 500,
        cursor: loading ? "not-allowed" : "pointer",
        flexShrink: 0,
        transition: "background 0.2s",
      }}
    >
      {loading ? "Extracting..." : "Extract Medicines"}
    </button>
  );
}
