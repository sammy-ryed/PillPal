"use client";

import { useCallback, useRef, useState } from "react";

interface Props {
  onFile: (file: File) => void;
}

export function UploadZone({ onFile }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files?.length) return;
      onFile(files[0]);
    },
    [onFile]
  );

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      style={{
        border: `2px dashed ${dragging ? "var(--color-terra)" : "rgba(42,37,32,0.15)"}`,
        borderRadius: 8,
        padding: "80px 40px",
        textAlign: "center",
        cursor: "pointer",
        transition: "border-color 0.2s, background 0.2s",
        background: dragging ? "rgba(196,92,58,0.03)" : "white",
      }}
    >
      {/* Icon */}
      <div
        style={{
          width: 72,
          height: 72,
          background: "var(--color-parchment)",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 24px",
        }}
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-warm-gray)" strokeWidth="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="12" y1="18" x2="12" y2="12" />
          <line x1="9" y1="15" x2="15" y2="15" />
        </svg>
      </div>

      <p
        style={{
          fontFamily: "var(--font-serif)",
          fontSize: "clamp(20px, 2.5vw, 26px)",
          marginBottom: 10,
        }}
      >
        Drop prescription here
      </p>
      <p style={{ fontSize: 14, color: "var(--color-warm-gray)", marginBottom: 28 }}>
        or click to browse from your device
      </p>

      <button
        onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}
        style={{
          background: "var(--color-terra)",
          color: "var(--color-cream)",
          border: "none",
          padding: "12px 28px",
          borderRadius: 4,
          fontFamily: "var(--font-sans)",
          fontSize: 15,
          fontWeight: 500,
          cursor: "pointer",
        }}
      >
        Choose File
      </button>

      <p
        style={{
          marginTop: 20,
          fontSize: 12,
          color: "var(--color-warm-gray)",
          fontFamily: "var(--font-mono)",
        }}
      >
        JPG · PNG · WEBP · BMP · up to 10 MB
      </p>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  );
}
