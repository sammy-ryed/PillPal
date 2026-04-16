import Link from "next/link";

export default function HomePage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        paddingTop: 120,
        paddingBottom: 80,
        paddingLeft: "clamp(20px, 5vw, 80px)",
        paddingRight: "clamp(20px, 5vw, 80px)",
        maxWidth: 1320,
        margin: "0 auto",
      }}
    >
      {/* Hero */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 80,
          alignItems: "center",
          marginBottom: 120,
        }}
      >
        <div>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              textTransform: "uppercase",
              letterSpacing: "0.15em",
              color: "var(--color-warm-gray)",
              marginBottom: 20,
            }}
          >
            Prescription Intelligence
          </div>
          <h1
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "clamp(40px, 5vw, 68px)",
              fontWeight: 400,
              lineHeight: 1.15,
              marginBottom: 24,
            }}
          >
            Your doctor wrote it.
            <br />
            <em style={{ color: "var(--color-terra)" }}>We read it.</em>
          </h1>
          <p
            style={{
              fontSize: 17,
              color: "var(--color-warm-gray)",
              lineHeight: 1.6,
              maxWidth: 440,
              marginBottom: 40,
            }}
          >
            Photograph any prescription. PillPal extracts every medicine, dose,
            and schedule — and sets up your reminders automatically.
          </p>
          <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
            <Link
              href="/upload"
              style={{
                background: "var(--color-terra)",
                color: "var(--color-cream)",
                padding: "14px 32px",
                borderRadius: 4,
                fontSize: 15,
                fontWeight: 500,
                textDecoration: "none",
              }}
            >
              Upload Prescription
            </Link>
            <Link
              href="/dashboard"
              style={{
                color: "var(--color-charcoal)",
                textDecoration: "none",
                fontSize: 15,
                borderBottom: "1px solid rgba(42,37,32,0.3)",
                paddingBottom: 1,
              }}
            >
              View Dashboard
            </Link>
          </div>

          {/* Stats */}
          <div
            style={{
              marginTop: 56,
              display: "flex",
              gap: 40,
              paddingTop: 32,
              borderTop: "1px solid rgba(42,37,32,0.1)",
            }}
          >
            {[
              { num: "6-stage", label: "OCR pipeline" },
              { num: "200+",    label: "Indian medicines" },
              { num: "< 8s",    label: "Parse time" },
            ].map(({ num, label }) => (
              <div key={label}>
                <div
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: 24,
                    color: "var(--color-charcoal)",
                  }}
                >
                  {num}
                </div>
                <div style={{ fontSize: 13, color: "var(--color-warm-gray)", marginTop: 2 }}>
                  {label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Prescription card visual */}
        <div
          style={{
            background: "white",
            borderRadius: 12,
            border: "1px solid rgba(42,37,32,0.1)",
            padding: 28,
            position: "relative",
          }}
        >
          {/* RX header */}
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 16,
              marginBottom: 24,
              paddingBottom: 20,
              borderBottom: "1px solid rgba(42,37,32,0.08)",
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                background: "var(--color-cream)",
                borderRadius: 8,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: "var(--font-serif)",
                fontSize: 20,
                color: "var(--color-terra)",
              }}
            >
              Rx
            </div>
            <div>
              <div style={{ fontWeight: 500, fontSize: 14 }}>Dr. S. Krishnan, MD</div>
              <div style={{ fontSize: 12, color: "var(--color-warm-gray)", marginTop: 2 }}>
                Apollo Hospitals · 26 Apr 2025
              </div>
            </div>
          </div>

          {/* Sample medicines */}
          {[
            { name: "Dolo 650",        dose: "650mg", freq: "BD",  days: "5d",  conf: 0.94 },
            { name: "Augmentin 625",   dose: "625mg", freq: "TDS", days: "7d",  conf: 0.89 },
            { name: "Pantoprazole 40", dose: "40mg",  freq: "OD",  days: "14d", conf: 0.91 },
          ].map((m, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "12px 0",
                borderBottom:
                  i < 2 ? "1px solid rgba(42,37,32,0.06)" : "none",
              }}
            >
              <div
                style={{
                  width: 4,
                  height: 32,
                  borderRadius: 4,
                  background: ["#C45C3A", "#7A9E8E", "#4A7060"][i],
                  flexShrink: 0,
                }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 500 }}>{m.name}</div>
                <div style={{ fontSize: 12, color: "var(--color-warm-gray)", marginTop: 2 }}>
                  {m.dose} · {m.freq} · {m.days}
                </div>
              </div>
              <span
                style={{
                  fontSize: 10,
                  fontFamily: "var(--font-mono)",
                  padding: "3px 8px",
                  borderRadius: 20,
                  background: "rgba(122,158,142,0.12)",
                  color: "var(--color-sage-dark)",
                }}
              >
                {Math.round(m.conf * 100)}%
              </span>
            </div>
          ))}

          {/* Floating tag */}
          <div
            style={{
              position: "absolute",
              top: -12,
              right: 20,
              background: "var(--color-sage)",
              color: "white",
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              padding: "6px 14px",
              borderRadius: 20,
            }}
          >
            Extracted
          </div>
        </div>
      </div>

      {/* Feature grid */}
      <div>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            textTransform: "uppercase",
            letterSpacing: "0.12em",
            color: "var(--color-warm-gray)",
            marginBottom: 16,
          }}
        >
          How it works
        </div>
        <h2
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "clamp(28px, 3vw, 40px)",
            fontWeight: 400,
            marginBottom: 48,
          }}
        >
          Three steps to never miss a dose
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 24,
          }}
        >
          {[
            {
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <circle cx="12" cy="12" r="4" />
                  <circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none" />
                </svg>
              ),
              title: "Photograph",
              desc:  "Take a clear photo of any prescription. Handwritten or printed, our OCR handles both.",
            },
            {
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" />
                </svg>
              ),
              title: "Extract",
              desc:  "Reads every medicine name, dosage, frequency and timing. Review and edit in seconds.",
            },
            {
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                  <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                </svg>
              ),
              title: "Remind",
              desc:  "Timely reminders at exactly the right time. Morning, afternoon, night, or custom.",
            },
          ].map(({ icon, title, desc }) => (
            <div
              key={title}
              style={{
                background: "white",
                borderRadius: 8,
                border: "1px solid rgba(42,37,32,0.08)",
                padding: 32,
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  background: "var(--color-parchment)",
                  borderRadius: 8,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: 20,
                  color: "var(--color-warm-gray)",
                }}
              >
                {icon}
              </div>
              <h3
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: 20,
                  fontWeight: 400,
                  marginBottom: 10,
                }}
              >
                {title}
              </h3>
              <p style={{ fontSize: 14, color: "var(--color-warm-gray)", lineHeight: 1.6 }}>
                {desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
