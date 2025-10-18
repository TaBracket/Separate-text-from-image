import { useState } from "react";
import { getHealth } from "./api";

export default function App() {
  const [health, setHealth] = useState(null);
  const [img, setImg] = useState(null);
  const [preview, setPreview] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error | ok

  const handleHealth = async () => {
    try {
      setStatus("loading");
      const data = await getHealth();
      setHealth(data);
      setStatus("ok");
    } catch (e) {
      setStatus("error");
      setHealth({ error: e.message });
    }
  };

  const handleFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImg(file);
    const url = URL.createObjectURL(file);
    setPreview(url);
  };

  return (
    <div
      style={{
        maxWidth: 900,
        margin: "40px auto",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h1 style={{ marginBottom: 8 }}>itt — OCR (English) — Frontend</h1>
      <p style={{ marginTop: 0, color: "#555" }}>
        Phase 1: UI skeleton (React, no TypeScript)
      </p>

      <section
        style={{
          marginTop: 24,
          padding: 16,
          border: "1px solid #eee",
          borderRadius: 12,
        }}
      >
        <h2 style={{ marginTop: 0 }}>Health Check</h2>
        <button
          onClick={handleHealth}
          style={{ padding: "8px 14px", borderRadius: 8, cursor: "pointer" }}
        >
          Call /api/health
        </button>
        <div
          style={{
            marginTop: 12,
            fontFamily: "ui-monospace, Menlo, monospace",
            whiteSpace: "pre-wrap",
          }}
        >
          {status === "idle" && (
            <span>Click the button to test backend...</span>
          )}
          {status === "loading" && <span>Loading...</span>}
          {status === "ok" && <code>{JSON.stringify(health, null, 2)}</code>}
          {status === "error" && (
            <span style={{ color: "crimson" }}>{health?.error}</span>
          )}
        </div>
      </section>

      <section
        style={{
          marginTop: 24,
          padding: 16,
          border: "1px solid #eee",
          borderRadius: 12,
        }}
      >
        <h2 style={{ marginTop: 0 }}>Upload Image (placeholder)</h2>
        <input type="file" accept="image/*" onChange={handleFile} />
        {preview && (
          <div style={{ marginTop: 12 }}>
            <img
              src={preview}
              alt="preview"
              style={{
                maxWidth: "100%",
                borderRadius: 8,
                border: "1px solid #ddd",
              }}
            />
          </div>
        )}
        <p style={{ color: "#777", marginTop: 12 }}>
          OCR endpoint will be wired in Phase 2.
        </p>
      </section>
    </div>
  );
}
