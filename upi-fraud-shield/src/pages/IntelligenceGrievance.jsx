import React, { useEffect, useState } from "react";
import { AlertCircle, FilePlus2, RefreshCw, ShieldCheck } from "lucide-react";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { DataLabel, DataNotice, ErrorPanel, PageHeading } from "../components/PagePrimitives";
import { apiService } from "../services/apiService";
import { formatDateTime } from "../utils/formatters";
import { useApiMode } from "../hooks/useApiMode";

const INTELLIGENCE_STATUSES = ["UNREVIEWED", "VERIFIED", "DISPUTED", "RETRACTED"];
const GRIEVANCE_STATUSES = ["UNDER_REVIEW", "MORE_INFO_REQUIRED", "RESOLVED", "REJECTED"];

export default function IntelligenceGrievance() {
  const { mode } = useApiMode();
  const [indicators, setIndicators] = useState([]);
  const [grievances, setGrievances] = useState([]);
  const [appeals, setAppeals] = useState({});
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [actionError, setActionError] = useState("");
  const [busyAction, setBusyAction] = useState("");
  const [reviewStatuses, setReviewStatuses] = useState({});
  const [indicatorForm, setIndicatorForm] = useState({
    indicator_type: "VPA",
    indicator_value: "",
    source: "",
    confidence: ""
  });

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [intelligenceResponse, grievanceResponse, assessmentResponse] = await Promise.all([
        apiService.getIntelligence({ limit: 100 }, mode),
        apiService.getGrievances({ limit: 100 }, mode),
        apiService.getRiskAssessments({ limit: 100 }, mode)
      ]);
      const indicatorItems = intelligenceResponse.data?.items;
      const grievanceItems = grievanceResponse.data?.items;
      const assessmentItems = assessmentResponse.data;
      if (!Array.isArray(indicatorItems) || !Array.isArray(grievanceItems) || !Array.isArray(assessmentItems)) {
        throw new Error("The backend returned an invalid investigation response.");
      }
      setIndicators(indicatorItems);
      setGrievances(grievanceItems);
      setAssessments(assessmentItems);
      const terminalGrievances = grievanceItems.filter((item) =>
        ["RESOLVED", "REJECTED"].includes(item.status)
      );
      const appealResponses = await Promise.all(
        terminalGrievances.map(async (item) => ({
          caseId: item.case_id,
          response: await apiService.getGrievanceAppeals(item.case_id, mode)
        }))
      );
      setAppeals(Object.fromEntries(
        appealResponses.map(({ caseId, response }) => [caseId, response.data?.items || []])
      ));
      setLastUpdated(new Date());
    } catch (requestError) {
      setIndicators([]);
      setGrievances([]);
      setAssessments([]);
      setAppeals({});
      setError(requestError.message || "Could not load intelligence and grievance records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [mode]);

  const submitIndicator = async (event) => {
    event.preventDefault();
    setActionError("");
    setBusyAction("indicator");
    try {
      await apiService.reportIntelligence(
        { ...indicatorForm, confidence: Number(indicatorForm.confidence) },
        mode
      );
      setIndicatorForm({ indicator_type: "VPA", indicator_value: "", source: "", confidence: "" });
      await loadData();
    } catch (requestError) {
      setActionError(requestError.message || "Could not report the indicator.");
    } finally {
      setBusyAction("");
    }
  };

  const submitGrievance = async (event) => {
    event.preventDefault();
    setActionError("");
    setBusyAction("grievance");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    try {
      await apiService.createGrievance(
        {
          user_reference: String(form.get("user_reference")).trim(),
          assessment_id: String(form.get("assessment_id")),
          reason: String(form.get("reason")).trim(),
          evidence_ref: String(form.get("evidence_ref") || "").trim() || null
        },
        mode
      );
      formElement.reset();
      await loadData();
    } catch (requestError) {
      setActionError(requestError.message || "Could not submit the grievance.");
    } finally {
      setBusyAction("");
    }
  };

  const updateIndicatorStatus = async (event, indicator) => {
    event.preventDefault();
    setActionError("");
    setBusyAction(indicator.indicator_id);
    try {
      const status = reviewStatuses[indicator.indicator_id] || indicator.review_status;
      await apiService.updateIntelligence(indicator.indicator_id, { review_status: status }, mode);
      await loadData();
    } catch (requestError) {
      setActionError(requestError.message || "Could not update the indicator review status.");
    } finally {
      setBusyAction("");
    }
  };

  const updateGrievance = async (event, grievance) => {
    event.preventDefault();
    setActionError("");
    setBusyAction(grievance.case_id);
    const form = new FormData(event.currentTarget);
    try {
      await apiService.updateGrievance(
        grievance.case_id,
        {
          status: String(form.get("status")),
          reviewer_note: String(form.get("reviewer_note")).trim()
        },
        mode
      );
      await loadData();
    } catch (requestError) {
      setActionError(requestError.message || "Could not update the grievance.");
    } finally {
      setBusyAction("");
    }
  };

  const submitAppeal = async (event, grievance) => {
    event.preventDefault();
    setActionError("");
    setBusyAction(`appeal-${grievance.case_id}`);
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    try {
      const response = await apiService.submitGrievanceAppeal(
        grievance.case_id,
        { reason: String(form.get("reason")).trim() },
        mode
      );
      setAppeals((current) => ({
        ...current,
        [grievance.case_id]: [
          ...(current[grievance.case_id] || []),
          response.data
        ]
      }));
      formElement.reset();
    } catch (requestError) {
      setActionError(requestError.message || "Could not submit the local appeal.");
    } finally {
      setBusyAction("");
    }
  };

  if (loading) {
    return <section className="surface-card"><LoadingSpinner message="Loading local review records..." subtext="The registry is synthetic and is not connected to an external fraud feed." /></section>;
  }

  if (error) {
    return <ErrorPanel title={mode === "MOCK" ? "Local API mode required" : "Investigation records unavailable"} error={error} onRetry={loadData} />;
  }

  return (
    <div className="space-y-6">
      <PageHeading
        eyebrow="Investigation workspace"
        title="Fraud Intelligence & Grievance Centre"
        description="Review locally stored indicators and internal prototype grievances. These records are not official findings or submissions to a bank."
        actions={
          <>
            <DataLabel />
            <button type="button" onClick={loadData} disabled={loading} className="rounded-md border border-outline-soft bg-white p-2 text-slate-600 hover:bg-surface-container disabled:opacity-60" aria-label="Refresh investigation records">
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </>
        }
      />

      <DataNotice tone="warning">
        <strong>Prototype workflow only.</strong> Indicator status is an internal review state, not independent confirmation. Grievances are stored locally and are not sent to a bank, NPCI, or law-enforcement agency.
      </DataNotice>

      <div className="grid gap-3 sm:grid-cols-3">
        <section className="surface-card p-4">
          <p className="text-xs text-slate-500">Stored indicators</p>
          <p className="mt-1 text-2xl font-semibold text-ink">{indicators.length.toLocaleString("en-IN")}</p>
        </section>
        <section className="surface-card p-4">
          <p className="text-xs text-slate-500">Prototype grievances</p>
          <p className="mt-1 text-2xl font-semibold text-ink">{grievances.length.toLocaleString("en-IN")}</p>
        </section>
        <section className="surface-card p-4">
          <p className="text-xs text-slate-500">Latest refresh</p>
          <p className="mt-2 text-sm font-semibold text-ink">{lastUpdated?.toLocaleTimeString() || "Not available"}</p>
        </section>
      </div>

      {actionError && (
        <div role="alert" className="flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-800">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {actionError}
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-2">
        <section className="surface-card p-4 sm:p-5">
          <div className="mb-4 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-brand-teal" />
            <div>
              <h3 className="text-sm font-semibold text-ink">Report an indicator</h3>
              <p className="text-[11px] text-slate-500">Adds a record to the local synthetic registry.</p>
            </div>
          </div>
          <form onSubmit={submitIndicator} className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-xs font-medium text-slate-600">
                Indicator type
                <select className="form-control mt-1.5" value={indicatorForm.indicator_type} onChange={(event) => setIndicatorForm({ ...indicatorForm, indicator_type: event.target.value })}>
                  <option value="VPA">VPA</option>
                  <option value="MOBILE">Mobile</option>
                  <option value="URL">URL</option>
                  <option value="DOMAIN">Domain</option>
                </select>
              </label>
              <label className="text-xs font-medium text-slate-600">
                Confidence (0–1)
                <input className="form-control mt-1.5" type="number" min="0" max="1" step="0.01" value={indicatorForm.confidence} onChange={(event) => setIndicatorForm({ ...indicatorForm, confidence: event.target.value })} required />
              </label>
            </div>
            <label className="block text-xs font-medium text-slate-600">
              Indicator value
              <input className="form-control mt-1.5" value={indicatorForm.indicator_value} onChange={(event) => setIndicatorForm({ ...indicatorForm, indicator_value: event.target.value })} minLength="2" maxLength="300" required />
            </label>
            <label className="block text-xs font-medium text-slate-600">
              Source label
              <input className="form-control mt-1.5" value={indicatorForm.source} onChange={(event) => setIndicatorForm({ ...indicatorForm, source: event.target.value })} minLength="2" maxLength="120" placeholder="e.g. User-submitted report" required />
            </label>
            <button type="submit" className="btn-primary" disabled={busyAction === "indicator"}>
              <FilePlus2 className="h-4 w-4" />
              {busyAction === "indicator" ? "Saving..." : "Add local indicator"}
            </button>
          </form>
        </section>

        <section className="surface-card p-4 sm:p-5">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-ink">Submit a prototype grievance</h3>
            <p className="text-[11px] text-slate-500">Requires an existing stored risk assessment; not an official complaint channel.</p>
          </div>
          {assessments.length ? (
            <form onSubmit={submitGrievance} className="space-y-3">
              <label className="block text-xs font-medium text-slate-600">
                User reference
                <input className="form-control mt-1.5" name="user_reference" maxLength="120" placeholder="Local user reference" required />
              </label>
              <label className="block text-xs font-medium text-slate-600">
                Related assessment
                <select className="form-control mt-1.5" name="assessment_id" defaultValue="" required>
                  <option value="" disabled>Select stored assessment</option>
                  {assessments.map((assessment) => (
                    <option key={assessment.assessment_id} value={assessment.assessment_id}>
                      {assessment.assessment_id} · {assessment.category} · score {assessment.score}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-xs font-medium text-slate-600">
                Reason
                <textarea className="form-control mt-1.5 min-h-20 resize-y" name="reason" minLength="10" maxLength="2000" required />
              </label>
              <label className="block text-xs font-medium text-slate-600">
                Evidence reference <span className="font-normal text-slate-400">(optional)</span>
                <input className="form-control mt-1.5" name="evidence_ref" maxLength="300" />
              </label>
              <button type="submit" className="btn-primary" disabled={busyAction === "grievance"}>
                <FilePlus2 className="h-4 w-4" />
                {busyAction === "grievance" ? "Submitting..." : "Save local grievance"}
              </button>
            </form>
          ) : (
            <EmptyState title="No assessments available" description="Analyze a test transaction first to create an assessment that can be referenced by this local workflow." />
          )}
        </section>
      </div>

      <section className="surface-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-outline-soft px-4 py-3 sm:px-5">
          <div>
            <h3 className="text-sm font-semibold text-ink">Indicator registry</h3>
            <p className="mt-0.5 text-[11px] text-slate-500">Review status applies only within this prototype.</p>
          </div>
          <span className="text-[10px] text-slate-500">{indicators.length} records</span>
        </div>
        {indicators.length ? (
          <div className="divide-y divide-slate-100">
            {indicators.map((indicator) => (
              <article key={indicator.indicator_id} className="grid gap-3 px-4 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:px-5">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded border border-outline-soft bg-canvas px-1.5 py-0.5 text-[9px] font-bold text-slate-600">{indicator.indicator_type}</span>
                    <span className="break-all font-mono text-xs font-semibold text-ink">{indicator.indicator_value}</span>
                    <span className="rounded border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[9px] font-semibold text-amber-800">{indicator.review_status}</span>
                  </div>
                  <p className="mt-1 text-[11px] text-slate-500">
                    Source: {indicator.source} · Confidence: {Math.round(indicator.confidence * 100)}% · Reported {formatDateTime(indicator.reported_at)}
                  </p>
                </div>
                <form onSubmit={(event) => updateIndicatorStatus(event, indicator)} className="flex gap-2">
                  <select
                    className="form-control min-w-32 py-2 text-xs"
                    value={reviewStatuses[indicator.indicator_id] || indicator.review_status}
                    onChange={(event) => setReviewStatuses({ ...reviewStatuses, [indicator.indicator_id]: event.target.value })}
                    aria-label={`Review status for ${indicator.indicator_id}`}
                  >
                    {INTELLIGENCE_STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}
                  </select>
                  <button type="submit" className="rounded-md border border-outline-soft bg-white px-3 text-xs font-semibold text-slate-700 hover:bg-canvas" disabled={busyAction === indicator.indicator_id}>
                    Save
                  </button>
                </form>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="No intelligence indicators stored" description="Reported indicators will appear here after they are saved to the local database." />
        )}
      </section>

      <section className="surface-card overflow-hidden">
        <div className="border-b border-outline-soft px-4 py-3 sm:px-5">
          <h3 className="text-sm font-semibold text-ink">Grievance review queue</h3>
        </div>
        {grievances.length ? (
          <div className="divide-y divide-slate-100">
            {grievances.map((grievance) => {
              const isTerminal = ["RESOLVED", "REJECTED"].includes(grievance.status);
              return (
                <article key={grievance.case_id} className="space-y-3 px-4 py-4 sm:px-5">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-mono text-xs font-semibold text-ink">{grievance.case_id}</p>
                      <p className="mt-1 text-xs text-slate-600">{grievance.reason}</p>
                    </div>
                    <span className="rounded border border-outline-soft bg-canvas px-2 py-1 text-[9px] font-bold text-slate-700">{grievance.status}</span>
                  </div>
                  <p className="text-[10px] text-slate-500">
                    Assessment: {grievance.assessment_id} · User reference: {grievance.user_reference} · Created {formatDateTime(grievance.created_at)}
                  </p>
                  {!isTerminal && (
                    <form onSubmit={(event) => updateGrievance(event, grievance)} className="grid gap-2 sm:grid-cols-[180px_minmax(0,1fr)_auto]">
                      <label className="sr-only" htmlFor={`grievance-status-${grievance.case_id}`}>New status</label>
                      <select id={`grievance-status-${grievance.case_id}`} className="form-control py-2 text-xs" name="status" defaultValue="UNDER_REVIEW">
                        {GRIEVANCE_STATUSES.map((status) => <option key={status} value={status}>{status.replaceAll("_", " ")}</option>)}
                      </select>
                      <label className="sr-only" htmlFor={`grievance-note-${grievance.case_id}`}>Reviewer note</label>
                      <input id={`grievance-note-${grievance.case_id}`} className="form-control py-2 text-xs" name="reviewer_note" minLength="1" maxLength="1000" placeholder="Internal reviewer note" required />
                      <button type="submit" className="rounded-md border border-outline-soft bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-canvas" disabled={busyAction === grievance.case_id}>
                        {busyAction === grievance.case_id ? "Saving..." : "Update"}
                      </button>
                    </form>
                  )}
                  {isTerminal && (
                    <div className="space-y-3 rounded-md border border-outline-soft bg-canvas/60 p-3">
                      <p className="text-[11px] font-semibold text-slate-700">Local appeals</p>
                      {(appeals[grievance.case_id] || []).map((appeal) => (
                        <div key={appeal.appeal_id} className="rounded border border-outline-soft bg-white p-2 text-[11px]">
                          <p className="font-mono text-slate-500">{appeal.appeal_id} · {appeal.status}</p>
                          <p className="mt-1 text-slate-700">{appeal.reason}</p>
                        </div>
                      ))}
                      <form onSubmit={(event) => submitAppeal(event, grievance)} className="space-y-2">
                        <label className="block text-[11px] font-medium text-slate-600">
                          Appeal reason
                          <textarea className="form-control mt-1 min-h-16" name="reason" minLength="10" maxLength="2000" required />
                        </label>
                        <button type="submit" className="rounded-md border border-outline-soft bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-canvas" disabled={busyAction === `appeal-${grievance.case_id}`}>
                          {busyAction === `appeal-${grievance.case_id}` ? "Submitting..." : "Submit local appeal"}
                        </button>
                      </form>
                    </div>
                  )}
                  {grievance.disclaimer && <p className="text-[10px] text-amber-800">{grievance.disclaimer}</p>}
                </article>
              );
            })}
          </div>
        ) : (
          <EmptyState title="No grievances stored" description="New local prototype grievances will appear in this queue." />
        )}
      </section>
    </div>
  );
}
