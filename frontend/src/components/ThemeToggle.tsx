import React, { useState } from "react";
import { useTheme } from "./ThemeContext";

export const ThemeToggle: React.FC = () => {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setShowMenu((v) => !v)}
        style={{
          padding: "0.4rem 0.7rem",
          borderRadius: "0.4rem",
          border: "1px solid var(--border)",
          background: "var(--bg-card)",
          color: "var(--text)",
          fontSize: "1rem",
          display: "flex",
          alignItems: "center",
          gap: "0.3rem",
        }}
        aria-label="Toggle theme"
        title={`Theme: ${theme}`}
      >
        {resolvedTheme === "light" ? "☀️" : "🌙"}
      </button>

      {showMenu && (
        <>
          <div
            onClick={() => setShowMenu(false)}
            style={{
              position: "fixed",
              inset: 0,
              zIndex: 9,
            }}
          />
          <div
            style={{
              position: "absolute",
              top: "calc(100% + 0.3rem)",
              right: 0,
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "0.4rem",
              boxShadow: "var(--shadow)",
              minWidth: "140px",
              zIndex: 10,
              overflow: "hidden",
            }}
          >
            {(["light", "dark", "system"] as const).map((opt) => (
              <button
                key={opt}
                onClick={() => {
                  setTheme(opt);
                  setShowMenu(false);
                }}
                style={{
                  width: "100%",
                  padding: "0.5rem 0.8rem",
                  border: "none",
                  background: theme === opt ? "var(--accent)" : "transparent",
                  color: theme === opt ? "#fff" : "var(--text)",
                  textAlign: "left",
                  fontSize: "0.85rem",
                  fontWeight: theme === opt ? 600 : 400,
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                {opt === "light" && "☀️"}
                {opt === "dark" && "🌙"}
                {opt === "system" && "🖥️"}
                <span style={{ textTransform: "capitalize" }}>{opt}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
