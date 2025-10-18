import React, { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5001";

export default function App() {
  const [pingResult, setPingResult] = useState(null);
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [postResult, setPostResult] = useState(null);
  const [error, setError] = useState("");

  const handlePing = async () => {
    setError("");
    setPingResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/ping`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPingResult(data);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setPostResult(null);
    setLoading(true);
    try {
      const form = new FormData();
      form.append("text", text);
      if (file) form.append("file", file);

      const res = await fetch(`${API_BASE}/api/process`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPostResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-4">
      <h1 className="mb-4">React + Bootstrap ↔ Python (Flask)</h1>

      {/* Ping Card */}
      <div className="card mb-4 shadow-sm">
        <div className="card-body">
          <h5 className="card-title">GET /api/ping</h5>
          <p className="card-text">اتصال سریع به بک‌اند Python و نمایش پاسخ.</p>
          <button className="btn btn-primary" onClick={handlePing}>
            تست اتصال
          </button>
          {pingResult && (
            <pre className="mt-3 bg-light p-3 rounded border">
              {JSON.stringify(pingResult, null, 2)}
            </pre>
          )}
        </div>
      </div>

      {/* POST Card */}
      <div className="card mb-4 shadow-sm">
        <div className="card-body">
          <h5 className="card-title">POST /api/process</h5>
          <p className="card-text">
            متن و/یا فایل آپلود کنید؛ جواب پردازشِ Python این پایین نمایش داده
            می‌شود.
          </p>
          <form onSubmit={handleSubmit} className="row g-3">
            <div className="col-12">
              <label className="form-label">متن</label>
              <input
                type="text"
                className="form-control"
                placeholder="مثلاً: hello OCR"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>

            <div className="col-12">
              <label className="form-label">فایل (اختیاری)</label>
              <input
                type="file"
                className="form-control"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <div className="form-text">
                در دنیای واقعی این‌جا OCR یا هر پردازشی را وصل کنید.
              </div>
            </div>

            <div className="col-12 d-flex gap-2">
              <button
                type="submit"
                className="btn btn-success"
                disabled={loading}
              >
                {loading ? "در حال ارسال..." : "ارسال به Python"}
              </button>
              <button
                type="button"
                className="btn btn-outline-secondary"
                onClick={() => {
                  setText("");
                  setFile(null);
                  setPostResult(null);
                  setError("");
                }}
              >
                ریست
              </button>
            </div>
          </form>

          {error && (
            <div className="alert alert-danger mt-3" role="alert">
              خطا: {error}
            </div>
          )}

          {postResult && (
            <pre className="mt-3 bg-light p-3 rounded border">
              {JSON.stringify(postResult, null, 2)}
            </pre>
          )}
        </div>
      </div>

      <footer className="text-muted">
        <small>
          Tip: آدرس سرور را با ENV تنظیم کنید: <code>VITE_API_BASE</code>
        </small>
      </footer>
    </div>
  );
}
