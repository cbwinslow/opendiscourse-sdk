import { useState } from "react";

export default function DiagnosticsPage() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);

  const fetchDiagnostics = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    setIngestStatus(null);
    try {
      const res = await fetch("/api/diagnostics/linux");
      if (!res.ok) throw new Error("Failed to fetch diagnostics");
      const data = await res.json();
      setReport(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const ingestDiagnostics = async () => {
    if (!report) return;
    setIngestStatus("Ingesting...");
    try {
      const res = await fetch("/api/ingest/diagnostics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report }),
      });
      if (!res.ok) throw new Error("Failed to ingest diagnostics");
      const data = await res.json();
      setIngestStatus(`Ingested! Report ID: ${data.report_id}`);
    } catch (e: any) {
      setIngestStatus(`Error: ${e.message}`);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "2rem auto", padding: 24 }}>
      <h1>Linux Diagnostics</h1>
      <button onClick={fetchDiagnostics} disabled={loading}>
        {loading ? "Collecting..." : "Collect Diagnostics"}
      </button>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {report && (
        <>
          <pre style={{ background: "#f4f4f4", padding: 16, marginTop: 16 }}>
            {JSON.stringify(report, null, 2)}
          </pre>
          <button onClick={ingestDiagnostics} style={{ marginTop: 16 }}>
            Ingest Report
          </button>
          {ingestStatus && <div style={{ marginTop: 8 }}>{ingestStatus}</div>}
        </>
      )}
    </div>
  );
}
