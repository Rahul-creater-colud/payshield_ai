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
  const [merchantId, setMerchantId] = useState("MERCH_DEMO_001");
  const [expectedAmount, setExpectedAmount] = useState("");
  const [callbackAmount, setCallbackAmount] = useState("");
  const [callbackStatus, setCallbackStatus] = useState("SUCCESS");
  const [ledgerSessionId, setLedgerSessionId] = useState("");
  const [ledgerResult, setLedgerResult] = useState(null);
  const [ledgerError, setLedgerError] = useState("");
  const [ledgerLoading, setLedgerLoading] = useState(false);

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

  const handleCreateLedgerSession = async (event) => {
    event.preventDefault();
    setLedgerLoading(true);
    setLedgerError("");
    setLedgerResult(null);
    try {
      const response = await apiService.createMerchantSession({
        merchant_id: merchantId.trim(),
        expected_amount: Number(expectedAmount)
      }, mode);
      setLedgerSessionId(response.data.session_id);
      setCallbackAmount(String(response.data.expected_amount));
      const verification = await apiService.getMerchantLedger(response.data.session_id, mode);
      setLedgerResult(verification.data);
    } catch (requestError) {
      setLedgerError(requestError.message || "Could not create a local merchant session.");
    } finally {
      setLedgerLoading(false);
    }
  };

  const handleVerifyLedger = async (event) => {
    event.preventDefault();
    setLedgerLoading(true);
    setLedgerError("");
    try {
      const response = await apiService.getMerchantLedger(ledgerSessionId.trim(), mode);
      setLedgerResult(response.data);
    } catch (requestError) {
      setLedgerResult(null);
      setLedgerError(requestError.message || "Could not verify the local merchant ledger.");
    } finally {
      setLedgerLoading(false);
    }
  };

  const handleSimulateCallback = async (event) => {
    event.preventDefault();
    setLedgerLoading(true);
    setLedgerError("");
    try {
      await apiService.simulatePaymentCallback(ledgerSessionId.trim(), {
        amount: Number(callbackAmount),
        status: callbackStatus
      }, mode);
      const response = await apiService.getMerchantLedger(ledgerSessionId.trim(), mode);
      setLedgerResult(response.data);
    } catch (requestError) {
      setLedgerError(requestError.message || "Could not record the simulated callback.");
    } finally {
      setLedgerLoading(false);
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
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-ink">Merchant ledger reconciliation</h3>
            <DataLabel>SIMULATED CALLBACKS ONLY</DataLabel>
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            Create a local expected-amount session, record an explicitly simulated callback, and compare the stored amount. This does not confirm a real payment.
          </p>
        </div>

        <form onSubmit={handleCreateLedgerSession} className="grid gap-3 sm:grid-cols-3">
          <label className="text-[11px] font-semibold text-slate-600">
            Merchant reference
            <input
              value={merchantId}
              onChange={(event) => setMerchantId(event.target.value)}
              required
              maxLength={100}
              className="form-control mt-1"
            />
          </label>
          <label className="text-[11px] font-semibold text-slate-600">
            Expected amount (₹)
            <input
              type="number"
              min="0.01"
              max="10000000"
              step="0.01"
              value={expectedAmount}
              onChange={(event) => setExpectedAmount(event.target.value)}
              required
              className="form-control mt-1"
            />
          </label>
          <div className="flex items-end">
            <button type="submit" className="btn-primary w-full" disabled={ledgerLoading || !merchantId.trim() || Number(expectedAmount) <= 0}>
              {ledgerLoading ? "Saving..." : "Create local session"}
            </button>
          </div>
        </form>

        <form onSubmit={handleVerifyLedger} className="grid gap-3 sm:grid-cols-[1fr_auto]">
          <label className="text-[11px] font-semibold text-slate-600">
            Session ID
            <input
              value={ledgerSessionId}
              onChange={(event) => setLedgerSessionId(event.target.value)}
              placeholder="e.g. SESS_001"
              required
              maxLength={100}
              className="form-control mt-1 font-mono"
            />
          </label>
          <button type="submit" className="btn-secondary" disabled={ledgerLoading || !ledgerSessionId.trim()}>
            Verify local ledger
          </button>
        </form>

        {ledgerSessionId.trim() && (
          <form onSubmit={handleSimulateCallback} className="grid gap-3 sm:grid-cols-[1fr_180px_auto]">
            <label className="text-[11px] font-semibold text-slate-600">
              Simulated callback amount (₹)
              <input
                type="number"
                min="0.01"
                max="10000000"
                step="0.01"
                value={callbackAmount}
                onChange={(event) => setCallbackAmount(event.target.value)}
                required
                className="form-control mt-1"
              />
            </label>
            <label className="text-[11px] font-semibold text-slate-600">
              Callback status
              <select value={callbackStatus} onChange={(event) => setCallbackStatus(event.target.value)} className="form-control mt-1">
                <option value="SUCCESS">Success (simulated)</option>
                <option value="FAILED">Failed (simulated)</option>
              </select>
            </label>
            <div className="flex items-end">
              <button type="submit" className="btn-secondary w-full" disabled={ledgerLoading || Number(callbackAmount) <= 0}>
                Record simulated callback
              </button>
            </div>
          </form>
        )}

        {ledgerLoading && <p className="text-xs text-slate-500">Checking local stored records...</p>}
        {ledgerError && <p role="alert" className="rounded border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{ledgerError}</p>}
        {ledgerResult && (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs">
            <p className="font-semibold text-slate-800">
              Ledger result: {ledgerResult.ledger_status.replaceAll("_", " ")}
            </p>
            <p className="mt-1 text-slate-600">
              Expected ₹{Number(ledgerResult.session.expected_amount).toFixed(2)}
              {ledgerResult.callback && ` · callback ₹${Number(ledgerResult.callback.amount).toFixed(2)} (${ledgerResult.callback.status})`}
            </p>
            <p className="mt-2 leading-relaxed text-amber-800">{ledgerResult.disclaimer}</p>
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
