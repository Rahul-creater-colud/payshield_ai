import React, { useEffect, useMemo, useState } from "react";
import { Search, Store, ShieldAlert, RefreshCw } from "lucide-react";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { DataLabel, DataNotice, ErrorPanel, PageHeading } from "../components/PagePrimitives";
import { useApiMode } from "../hooks/useApiMode";
import { apiService } from "../services/apiService";

export default function MerchantVerification() {
  const { mode } = useApiMode();
  const [accounts, setAccounts] = useState([]);
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [merchantId, setMerchantId] = useState("");
  const [expectedAmount, setExpectedAmount] = useState("");
  const [sessionReference, setSessionReference] = useState("");
  const [paymentSession, setPaymentSession] = useState(null);
  const [sessionError, setSessionError] = useState("");
  const [sessionLoading, setSessionLoading] = useState(false);

  const loadCatalog = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await apiService.getCatalog(mode);
      if (!Array.isArray(response.data?.accounts)) {
        throw new Error("The backend returned an invalid local account catalog.");
      }
      setAccounts(response.data.accounts);
      setLastUpdated(new Date());
    } catch (requestError) {
      setAccounts([]);
      setError(requestError.message || "Could not load the local account catalog.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCatalog();
  }, [mode]);

  const matches = useMemo(() => {
    const term = submittedQuery.trim().toLowerCase();
    if (!term) return [];
    return accounts.filter((account) =>
      [account.account_id, account.vpa, account.label]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(term))
    );
  }, [accounts, submittedQuery]);

  const handleSearch = (event) => {
    event.preventDefault();
    if (!query.trim()) {
      setSearched(false);
      setSubmittedQuery("");
      return;
    }
    setSubmittedQuery(query.trim());
    setSearched(true);
  };

  const createSession = async (event) => {
    event.preventDefault();
    setSessionError("");
    setSessionLoading(true);
    try {
      const response = await apiService.createMerchantSession({
        merchant_id: merchantId.trim(),
        expected_amount: Number(expectedAmount)
      }, mode);
      setPaymentSession(response.data);
      setSessionReference(response.data.session_id);
    } catch (requestError) {
      setSessionError(requestError.message || "Could not create a demo payment session.");
    } finally {
      setSessionLoading(false);
    }
  };

  const lookupSession = async (event) => {
    event.preventDefault();
    setSessionError("");
    setSessionLoading(true);
    try {
      const response = await apiService.getMerchantTransaction(sessionReference.trim(), mode);
      setPaymentSession(response.data);
    } catch (requestError) {
      setPaymentSession(null);
      setSessionError(requestError.message || "Could not find that merchant session.");
    } finally {
      setSessionLoading(false);
    }
  };

  const recordSimulatedResult = async (status) => {
    if (!paymentSession) return;
    setSessionError("");
    setSessionLoading(true);
    try {
      const response = await apiService.simulatePaymentCallback({
        session_id: paymentSession.session_id,
        merchant_id: paymentSession.merchant_id,
        amount: paymentSession.expected_amount,
        status
      }, mode);
      setPaymentSession(response.data);
    } catch (requestError) {
      setSessionError(requestError.message || "Could not record the simulated status.");
    } finally {
      setSessionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeading
        eyebrow="Merchant review"
        title="Merchant Verification"
        description="Search records held in the local prototype catalog. A local match is not proof of merchant identity or registration."
        actions={
          <>
            <DataLabel>Local synthetic catalog</DataLabel>
            <button type="button" onClick={loadCatalog} disabled={loading} className="rounded-md border border-outline-soft bg-white p-2 text-slate-600 hover:bg-surface-container disabled:opacity-60" aria-label="Refresh merchant catalog">
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </>
        }
      />

      <DataNotice tone="warning">
        <strong>No external merchant registry is connected.</strong> PayShield cannot verify a business with a bank, NPCI, PSP, or government registry. The catalog below contains synthetic account references only.
      </DataNotice>

      <section className="surface-card space-y-4 p-5 sm:p-6">
        <div>
          <h3 className="text-sm font-semibold text-ink">Demo payment-status ledger</h3>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            Create a persisted local reference, look it up, or record one simulated callback. A simulated SUCCESS is not a payment confirmation.
          </p>
        </div>
        {mode !== "LIVE" && (
          <p role="status" className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            Switch to LOCAL API mode to use the backend-backed demo ledger.
          </p>
        )}
        <form onSubmit={createSession} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <label className="text-xs font-medium text-slate-700">
            Merchant reference
            <input
              className="form-control mt-1"
              value={merchantId}
              onChange={(event) => setMerchantId(event.target.value)}
              maxLength={128}
              required
              placeholder="DEMO-MERCHANT-01"
            />
          </label>
          <label className="text-xs font-medium text-slate-700">
            Expected amount (₹)
            <input
              className="form-control mt-1"
              type="number"
              min="0.01"
              max="1000000"
              step="0.01"
              value={expectedAmount}
              onChange={(event) => setExpectedAmount(event.target.value)}
              required
              placeholder="500.00"
            />
          </label>
          <button type="submit" className="btn-primary self-end" disabled={sessionLoading || mode !== "LIVE"}>
            {sessionLoading ? "Saving..." : "Create demo session"}
          </button>
        </form>

        <form onSubmit={lookupSession} className="flex flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor="merchant-session-reference">Session reference</label>
          <input
            id="merchant-session-reference"
            className="form-control min-w-0 flex-1"
            value={sessionReference}
            onChange={(event) => setSessionReference(event.target.value)}
            required
            placeholder="Look up a session ID"
          />
          <button type="submit" className="btn-secondary" disabled={sessionLoading || mode !== "LIVE"}>
            Look up session
          </button>
        </form>

        {sessionError && (
          <p role="alert" className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            {sessionError}
          </p>
        )}
        {paymentSession && (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="break-all font-mono text-xs font-semibold text-ink">{paymentSession.session_id}</p>
                <p className="mt-1 text-xs text-slate-600">
                  Merchant: {paymentSession.merchant_id} · Expected: ₹{Number(paymentSession.expected_amount).toLocaleString("en-IN")}
                </p>
              </div>
              <span className="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-[10px] font-bold uppercase text-amber-800">
                {paymentSession.status} · DEMO
              </span>
            </div>
            <p className="mt-2 text-[11px] leading-5 text-amber-800">{paymentSession.disclaimer}</p>
            {paymentSession.status === "PENDING" && (
              <div className="mt-3 flex flex-wrap gap-2">
                <button type="button" className="btn-secondary" disabled={sessionLoading} onClick={() => recordSimulatedResult("SUCCESS")}>
                  Record simulated success
                </button>
                <button type="button" className="btn-secondary" disabled={sessionLoading} onClick={() => recordSimulatedResult("FAILED")}>
                  Record simulated failure
                </button>
              </div>
            )}
            {paymentSession.status_history?.length > 0 && (
              <ul className="mt-3 space-y-1 border-t border-slate-200 pt-3 text-[11px] text-slate-600">
                {paymentSession.status_history.map((item) => (
                  <li key={item.event_id}>
                    {item.status} · {item.recorded_at} · simulated
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>

      {loading ? (
        <section className="surface-card">
          <LoadingSpinner message="Loading local account catalog..." subtext="No external verification service is contacted." />
        </section>
      ) : error ? (
        <ErrorPanel title={mode === "MOCK" ? "Local API mode required" : "Merchant catalog unavailable"} error={error} onRetry={loadCatalog} />
      ) : (
        <>
          <section className="surface-card p-5 sm:p-6">
            <div className="mb-4 flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-teal-50 text-brand-teal">
                <Store className="h-5 w-5" />
              </span>
              <div>
                <h3 className="text-sm font-semibold text-ink">Search local account references</h3>
                <p className="text-xs text-slate-500">Search by account ID or stored VPA; no verification decision is made.</p>
              </div>
            </div>
            <form onSubmit={handleSearch} className="flex flex-col gap-2 sm:flex-row">
              <label className="sr-only" htmlFor="merchant-query">Account ID or VPA</label>
              <div className="relative min-w-0 flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  id="merchant-query"
                  className="form-control pl-9"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Enter an account ID or VPA"
                  autoComplete="off"
                />
              </div>
              <button type="submit" className="btn-primary" disabled={!query.trim()}>
                Search local records
              </button>
            </form>
            <p className="mt-3 text-[11px] text-slate-500">
              Catalog records: {accounts.length.toLocaleString("en-IN")} · Updated {lastUpdated?.toLocaleTimeString() || "not available"}
            </p>
          </section>

          {searched ? (
            matches.length ? (
              <section className="space-y-3">
                <h3 className="text-sm font-semibold text-ink">Local matches ({matches.length})</h3>
                <div className="grid gap-3 md:grid-cols-2">
                  {matches.map((account) => (
                    <article key={account.account_id} className="surface-card p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="break-all font-mono text-sm font-semibold text-ink">{account.vpa || account.account_id}</p>
                          <p className="mt-1 text-xs text-slate-500">Account reference: {account.account_id}</p>
                        </div>
                        <span className="shrink-0 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-[9px] font-bold uppercase text-amber-800">
                          Not verified
                        </span>
                      </div>
                      <p className="mt-3 border-t border-slate-100 pt-3 text-xs leading-5 text-slate-600">
                        Record found in the synthetic local catalog. No merchant ownership or external registration was checked.
                      </p>
                    </article>
                  ))}
                </div>
              </section>
            ) : (
              <EmptyState
                icon={ShieldAlert}
                title="No local account match"
                description="No matching account reference exists in the current local catalog. This does not indicate whether a real merchant is legitimate."
              />
            )
          ) : (
            <section className="surface-card flex flex-col items-center px-6 py-10 text-center">
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-container text-slate-500">
                <Store className="h-6 w-6" />
              </span>
              <h3 className="mt-3 text-sm font-semibold text-ink">Merchant verification is unavailable</h3>
              <p className="mt-1 max-w-lg text-xs leading-5 text-slate-500">
                Use the local lookup only to inspect a synthetic account record. Authoritative merchant verification requires an approved external integration.
              </p>
            </section>
          )}
        </>
      )}
    </div>
  );
}
