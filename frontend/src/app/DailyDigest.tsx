"use client";
import { useState } from "react";

export default function DailyDigest() {
  const [digest, setDigest] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function fetchDigest() {
    setLoading(true);
    setError("");
    setDigest("");
    try {
      const res = await fetch("/api/daily-digest");
      if (!res.ok) throw new Error("Failed to fetch digest");
      const data = await res.text();
      setDigest(data);
    } catch (e) {
    if (e instanceof Error) {
      setError(e.message);
    } else {
      setError("Unknown error");
    }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: "2rem auto", padding: 24, border: "1px solid #eee", borderRadius: 12, background: "#fafbfc" }}>
      <h2>Daily Gmail Digest</h2>
      <button onClick={fetchDigest} disabled={loading} style={{ padding: "0.5rem 1.5rem", fontSize: 18, borderRadius: 6, background: "#0070f3", color: "white", border: "none", cursor: loading ? "not-allowed" : "pointer" }}>
        {loading ? "Loading..." : "Get My Summary"}
      </button>
      {error && <div style={{ color: "red", marginTop: 16 }}>{error}</div>}
      {digest && (
        <div style={{ marginTop: 32 }}>
          <pre style={{ whiteSpace: "pre-wrap", background: "#f5f5f5", padding: 16, borderRadius: 8 }}>{digest}</pre>
        </div>
      )}
    </div>
  );
}
