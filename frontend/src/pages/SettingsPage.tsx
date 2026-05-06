import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/PageHeader";

const API_KEY_STORAGE = "vectaris_api_key";

export const SettingsPage: React.FC = () => {
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    setApiKey(localStorage.getItem(API_KEY_STORAGE) ?? "");
  }, []);

  const handleSave = () => {
    if (apiKey.trim()) {
      localStorage.setItem(API_KEY_STORAGE, apiKey.trim());
    } else {
      localStorage.removeItem(API_KEY_STORAGE);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleClear = () => {
    localStorage.removeItem(API_KEY_STORAGE);
    setApiKey("");
  };

  return (
    <>
      <PageHeader
        title="Settings"
        subtitle="Configure authentication and display preferences"
      />

      <div
        className="card"
        style={{ maxWidth: "540px", display: "flex", flexDirection: "column", gap: "1rem" }}
      >
        <h3 style={{ margin: 0, fontSize: "1rem" }}>API Authentication</h3>
        <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-muted)" }}>
          Enter your <code>X-API-Key</code> here. It is stored only in your
          browser's <code>localStorage</code> and sent with every API request.
          Leave empty if the backend runs without authentication.
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
          <label htmlFor="api-key-input" style={{ fontSize: "0.85rem", fontWeight: 600 }}>
            API Key
          </label>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              id="api-key-input"
              type={showKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-…"
              autoComplete="off"
              style={{
                flex: 1,
                padding: "0.45rem 0.7rem",
                borderRadius: "0.4rem",
                border: "1px solid var(--border, #2e2e40)",
                background: "var(--surface-2, #1e1e2e)",
                color: "var(--text, #e2e8f0)",
                fontSize: "0.85rem",
                fontFamily: "monospace",
              }}
            />
            <button
              onClick={() => setShowKey((v) => !v)}
              style={{
                padding: "0.45rem 0.7rem",
                borderRadius: "0.4rem",
                border: "1px solid var(--border, #2e2e40)",
                background: "var(--surface-2, #1e1e2e)",
                color: "var(--text-muted)",
                cursor: "pointer",
                fontSize: "0.8rem",
              }}
            >
              {showKey ? "Hide" : "Show"}
            </button>
          </div>
        </div>

        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <button
            onClick={handleSave}
            style={{
              padding: "0.45rem 1rem",
              borderRadius: "0.4rem",
              border: "none",
              background: "var(--accent, #7c3aed)",
              color: "#fff",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.85rem",
            }}
          >
            Save
          </button>
          <button
            onClick={handleClear}
            style={{
              padding: "0.45rem 0.8rem",
              borderRadius: "0.4rem",
              border: "1px solid var(--border, #2e2e40)",
              background: "transparent",
              color: "var(--text-muted)",
              cursor: "pointer",
              fontSize: "0.85rem",
            }}
          >
            Clear
          </button>
          {saved && (
            <span style={{ fontSize: "0.82rem", color: "var(--success, #22c55e)" }}>
              ✓ Saved
            </span>
          )}
        </div>
      </div>

      <div
        className="card"
        style={{ maxWidth: "540px", marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.6rem" }}
      >
        <h3 style={{ margin: 0, fontSize: "1rem" }}>About</h3>
        <table style={{ fontSize: "0.82rem", borderCollapse: "collapse", width: "100%" }}>
          <tbody>
            <tr>
              <td style={{ padding: "0.2rem 0.5rem 0.2rem 0", color: "var(--text-muted)", width: "40%" }}>Version</td>
              <td>1.0.0</td>
            </tr>
            <tr>
              <td style={{ padding: "0.2rem 0.5rem 0.2rem 0", color: "var(--text-muted)" }}>API Base URL</td>
              <td>
                <code style={{ fontSize: "0.8rem" }}>
                  {import.meta.env.VITE_API_URL ?? "http://localhost:8000"}
                </code>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
};
