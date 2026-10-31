import React, { useState } from "react";
import { AlertTriangle, CheckCircle2, Link2, Search, ShieldAlert } from "lucide-react";
import { DataLabel, DataNotice, ErrorPanel, PageHeading } from "../components/PagePrimitives";
import { apiService } from "../services/apiService";
import { useApiMode } from "../hooks/useApiMode";

const verdictStyles = {
  SAFE: "border-emerald-200 bg-emerald-50 text-emerald-800",
  SUSPICIOUS: "border-amber-200 bg-amber-50 text-amber-900",
  MALICIOUS: "border-rose-200 bg-rose-50 text-rose-900",
  INVALID: "border-slate-200 bg-slate-50 text-slate-700"
};

export default function SuspiciousUrlScanner() {
  const { mode } = useApiMode();
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const scan = async (event) => {
    event.preventDefault();
    if (!url.trim()) {
      setError("Enter a URL to scan.");
      setResult(null);
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await apiService.scanUrl(url.trim(), mode);
      if (!response.data || typeof response.data.verdict !== "string" || !Array.isArray(response.data.indicators)) {
        throw new Error("The backend returned an invalid URL scan response.");
      }
      setResult(response.data);
      setLastUpdated(new Date());
    } catch (requestError) {
      setError(requestError.message || "The URL could not be scanned.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeading
        eyebrow="Link analysis"
        title="Suspicious URL Scanner"
        description="Review URL characteristics with local static rules and stored indicators. PayShield does not open, fetch, or visit submitted URLs."
        actions={<DataLabel />}
      />

      <DataNotice tone="warning">
        This is a local heuristic screen, not a live threat-intelligence feed. A SAFE result is not a guarantee, and HTTPS does not prove a site is legitimate.
      </DataNotice>

      <section className="surface-card p-5 sm:p-7">
        <div className="mx-auto max-w-3xl">
          <div className="mb-5 text-center">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-teal-50 text-brand-teal">
              <Link2 className="h-6 w-6" />
            </span>
            <h3 className="mt-3 text-base font-semibold text-ink">Analyze a link</h3>
            <p className="mt-1 text-xs text-slate-500">No network request is made to the submitted destination.</p>
          </div>
          <form onSubmit={scan} className="space-y-3">
            <label htmlFor="url-input" className="block text-xs font-medium text-slate-600">URL or domain</label>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                id="url-input"
                className="form-control min-w-0 flex-1"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example.com/path"
                autoComplete="url"
                required
              />
              <button type="submit" className="btn-primary" disabled={loading}>
                <Search className="h-4 w-4" />
                {loading ? "Scanning..." : "Scan URL"}
              </button>
            </div>
          </form>
          {error && <p role="alert" className="mt-3 text-xs text-rose-700">{error}</p>}
        </div>
      </section>

      {loading && <section className="surface-card p-6 text-center text-sm text-slate-500">Checking URL structure and local indicators…</section>}
      {!loading && error && <ErrorPanel title={mode === "MOCK" ? "Local API mode required" : "URL scan unavailable"} error={error} />}

      {result && (
        <div className="space-y-4">
          <section className={`rounded-md border p-4 sm:p-5 ${verdictStyles[result.verdict] || verdictStyles.INVALID}`}>
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <div className="flex items-start gap-3">
                <span className="mt-0.5">
                  {result.verdict === "SAFE" ? <CheckCircle2 className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
                </span>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide">Heuristic verdict</p>
                  <h3 className="mt-0.5 text-xl font-bold">{result.verdict}</h3>
                  <p className="mt-1 break-all font-mono text-xs">{result.normalized_url}</p>
                </div>
              </div>
              <div className="sm:text-right">
                <p className="text-xs font-medium">Local rule score</p>
                <p className="text-3xl font-semibold">{result.risk_score}<span className="text-base font-medium">/100</span></p>
              </div>
            </div>
            <p className="mt-4 border-t border-current/10 pt-3 text-xs leading-5">{result.advice}</p>
          </section>

          <section className="surface-card p-4 sm:p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-ink">Indicators found</h3>
                <p className="mt-1 text-xs text-slate-500">Rule outputs only; not a confirmed threat classification.</p>
              </div>
              <span className="text-[10px] text-slate-500">Updated {lastUpdated?.toLocaleTimeString() || "not available"}</span>
            </div>
            {result.indicators.length ? (
              <ul className="mt-3 divide-y divide-slate-100">
                {result.indicators.map((indicator, index) => (
                  <li key={`${indicator.code}-${index}`} className="flex gap-2 py-3 text-xs leading-5 text-slate-700">
                    <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-brand-teal" />
                    <span>{indicator.text}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 rounded-md bg-canvas p-3 text-xs text-slate-600">No indicators were returned by the local rules.</p>
            )}
          </section>
          <p className="text-[11px] leading-5 text-slate-500">{result.disclaimer || "Local heuristic prototype. Risk scores are illustrative, not proof of fraud."}</p>
        </div>
      )}
    </div>
  );
}
