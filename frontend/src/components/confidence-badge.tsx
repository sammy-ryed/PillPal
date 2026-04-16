import type { ConfidenceLevel } from "@/lib/types";

const styles: Record<ConfidenceLevel, React.CSSProperties> = {
  high: {
    background: "rgba(122,158,142,0.15)",
    color: "var(--color-sage-dark)",
  },
  medium: {
    background: "rgba(196,92,58,0.1)",
    color: "var(--color-terra)",
  },
  low: {
    background: "rgba(138,131,122,0.12)",
    color: "var(--color-warm-gray)",
  },
};

interface Props {
  score: number;
}

export function ConfidenceBadge({ score }: Props) {
  const level: ConfidenceLevel =
    score >= 0.85 ? "high" : score >= 0.6 ? "medium" : "low";

  return (
    <span
      style={{
        ...styles[level],
        fontSize: 11,
        fontFamily: "var(--font-mono)",
        padding: "4px 10px",
        borderRadius: 20,
        fontWeight: 500,
        whiteSpace: "nowrap",
      }}
    >
      {Math.round(score * 100)}% match
    </span>
  );
}
