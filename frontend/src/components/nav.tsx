"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/",          label: "Home" },
  { href: "/upload",    label: "Upload" },
  { href: "/dashboard", label: "Dashboard" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "20px 40px",
        background: "var(--color-cream)",
        borderBottom: "1px solid rgba(42,37,32,0.1)",
      }}
    >
      <Link
        href="/"
        style={{
          fontFamily: "var(--font-serif)",
          fontSize: 22,
          color: "var(--color-charcoal)",
          textDecoration: "none",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <LogoPill />
        PillPal
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
        {links.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            style={{
              textDecoration: "none",
              fontSize: 14,
              fontWeight: 400,
              color:
                pathname === href
                  ? "var(--color-charcoal)"
                  : "var(--color-warm-gray)",
              transition: "color 0.2s",
            }}
          >
            {label}
          </Link>
        ))}
        <Link
          href="/upload"
          style={{
            background: "var(--color-charcoal)",
            color: "var(--color-cream)",
            padding: "9px 20px",
            borderRadius: 4,
            fontSize: 14,
            fontWeight: 500,
            textDecoration: "none",
            transition: "background 0.2s",
          }}
        >
          Get Started
        </Link>
      </div>
    </nav>
  );
}

function LogoPill() {
  return (
    <div
      style={{
        width: 28,
        height: 16,
        background: "var(--color-terra)",
        borderRadius: 20,
        position: "relative",
        flexShrink: 0,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%,-50%)",
          width: 1,
          height: "100%",
          background: "rgba(247,243,238,0.6)",
        }}
      />
    </div>
  );
}
