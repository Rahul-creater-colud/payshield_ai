import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Filter,
  FileText,
  Download,
  PhoneCall,
  Clock,
  ArrowRight,
  ShieldCheck,
  Check,
  Printer,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import ConfirmationModal from "../components/ConfirmationModal";
import EmptyState from "../components/EmptyState";
import { apiService } from "../services/apiService";
import { useApiMode } from "../hooks/useApiMode";
import { useToast } from "../hooks/useToast";
import { formatCurrency, formatDateTime } from "../utils/formatters";

export const AlertsRiskReport = () => {
  const { mode } = useApiMode();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [severityFilter, setSeverityFilter] = useState("ALL"); // ALL, HIGH, MEDIUM, LOW
  const [expandedAlertId, setExpandedAlertId] = useState(null);
  const [resolveModalAlert, setResolveModalAlert] = useState(null);
  const [resolveNotes, setResolveNotes] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, [mode]);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await apiService.getFraudAlerts(mode);
      const data = res.data || res;
      setAlerts(data.data || []);
      setSummary(data.summary || null);
    } catch (err) {
      console.error("Failed to load alerts:", err);
      toast.error("Failed to fetch threat alerts", "Error");
    } finally {
      setLoading(false);
    }
  };

  const handleResolveConfirm = async () => {
    if (!resolveModalAlert) return;
    setActionLoading(true);
    try {
      await apiService.resolveAlert(resolveModalAlert.id, resolveNotes, mode);
      toast.success(`Alert ${resolveModalAlert.id} marked as resolved`, "Incident Cleared");
      setResolveModalAlert(null);
      setResolveNotes("");
      fetchAlerts();
    } catch (err) {
      toast.error("Failed to resolve alert", "Error");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePrintReport = () => {
    window.print();
  };

  const handleExportJSON = () => {
    const reportData = {
      generatedAt: new Date().toISOString(),
      summary,
      alerts
    };
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `upi-fraud-risk-report-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("Risk dossier exported to JSON", "Export Complete");
  };

  const filteredAlerts = alerts.filter((a) => {
    if (severityFilter === "ALL") return true;
    return a.category === severityFilter;
  });

  if (loading) {
    return <LoadingSpinner message="Generating threat intelligence & incident report..." />;
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto animate-fade-in print:p-0">
      {/* Header and Print/Export Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
            Fraud Alerts & Security Risk Report
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Centralized incident log, root cause forensic explanations, and recommended defensive actions.
          </p>
        </div>

        <div className="flex items-center gap-2 print:hidden">
          <button
            onClick={handleExportJSON}
            className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-xs transition flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export JSON</span>
          </button>

          <button
            onClick={handlePrintReport}
            className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Dashboard Section */}
      {summary && (
        <div className="rounded-3xl bg-white border border-slate-200/90 p-6 lg:p-7 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Threat Intelligence Summary
              </span>
              <h3 className="text-base font-bold text-slate-900 mt-0.5">
                24-Hour Digital Payment Risk Audit
              </h3>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
              Confidence Score: {summary.modelConfidenceScore}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] font-bold uppercase text-slate-400 block">Total Alerts Today</span>
              <div className="text-2xl font-extrabold text-slate-900 mt-1">{summary.totalAlertsToday}</div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">18 active investigations</span>
            </div>

            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-100">
              <span className="text-[10px] font-bold uppercase text-rose-700 block">Critical High Threats</span>
              <div className="text-2xl font-extrabold text-rose-900 mt-1">{summary.criticalHighAlerts}</div>
              <span className="text-[11px] text-rose-700 font-semibold mt-0.5 block">Immediate action required</span>
            </div>

            <div className="p-4 rounded-2xl bg-amber-50 border border-amber-100">
              <span className="text-[10px] font-bold uppercase text-amber-700 block">Medium Suspicion</span>
              <div className="text-2xl font-extrabold text-amber-900 mt-1">{summary.mediumAlerts}</div>
              <span className="text-[11px] text-amber-700 font-semibold mt-0.5 block">Step-up challenge sent</span>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100">
              <span className="text-[10px] font-bold uppercase text-emerald-700 block">Fraud Intercepted</span>
              <div className="text-2xl font-extrabold text-emerald-900 mt-1">{summary.fraudPreventedAmount}</div>
              <span className="text-[11px] text-emerald-700 font-semibold mt-0.5 block">Prevented user loss</span>
            </div>
          </div>

          {/* Primary Fraud Vector callout */}
          <div className="mt-5 p-4 rounded-2xl bg-navy-950 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">
                Top Threat Vector Identified
              </span>
              <p className="text-sm font-bold mt-0.5">{summary.topVector}</p>
            </div>
            <div className="text-xs text-slate-300">
              Average AI Latency: <span className="font-mono font-bold text-cyan-300">{summary.avgDetectionLatencyMs}ms</span>
            </div>
          </div>
        </div>
      )}

      {/* Safety Safeguards & Recommendations Section */}
      {summary && summary.safeguardRecommendations && (
        <div className="rounded-3xl bg-blue-50/70 border border-blue-200/80 p-6">
          <h3 className="text-sm font-bold uppercase tracking-wider text-blue-950 flex items-center gap-2 mb-3">
            <ShieldCheck className="w-5 h-5 text-blue-600" /> Mandatory Consumer Safety Directives:
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {summary.safeguardRecommendations.map((rec, i) => (
              <div
                key={i}
                className="p-3.5 rounded-xl bg-white border border-blue-100 text-xs text-slate-700 font-medium flex items-start gap-2.5 shadow-2xs"
              >
                <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Tabs for Alerts List */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <h3 className="text-base font-bold text-slate-900">Incident Dossiers & Threat Logs</h3>

        <div className="flex items-center gap-2">
          {["ALL", "HIGH", "MEDIUM", "LOW"].map((cat) => (
            <button
              key={cat}
              onClick={() => setSeverityFilter(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition border ${
                severityFilter === cat
                  ? cat === "HIGH"
                    ? "bg-rose-600 text-white border-rose-600 shadow-sm"
                    : cat === "MEDIUM"
                    ? "bg-amber-500 text-white border-amber-500 shadow-sm"
                    : cat === "LOW"
                    ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                    : "bg-slate-900 text-white border-slate-900 shadow-sm"
                  : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
              }`}
            >
              {cat === "ALL" ? "All Severities" : `${cat} Risk`}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      {filteredAlerts.length === 0 ? (
        <EmptyState
          title="No Alerts in this Category"
          description={`No threat alerts currently recorded under ${severityFilter} severity.`}
        />
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map((alert) => {
            const isExpanded = expandedAlertId === alert.id;
            const isHigh = alert.category === "HIGH";
            const isResolved = alert.status === "RESOLVED";

            return (
              <div
                key={alert.id}
                className={`rounded-2xl border transition-all ${
                  isHigh && !isResolved
                    ? "bg-white border-rose-200 shadow-md shadow-rose-500/5 hover:border-rose-300"
                    : isResolved
                    ? "bg-slate-50/70 border-slate-200 opacity-80"
                    : "bg-white border-slate-200/90 shadow-sm"
                }`}
              >
                {/* Header row */}
                <div
                  onClick={() => setExpandedAlertId(isExpanded ? null : alert.id)}
                  className="p-5 cursor-pointer flex flex-col lg:flex-row lg:items-center justify-between gap-4"
                >
                  <div className="flex items-start gap-3.5">
                    <div
                      className={`p-2.5 rounded-xl border shrink-0 mt-0.5 ${
                        isHigh
                          ? "bg-rose-50 text-rose-600 border-rose-200"
                          : alert.category === "MEDIUM"
                          ? "bg-amber-50 text-amber-600 border-amber-200"
                          : "bg-emerald-50 text-emerald-600 border-emerald-200"
                      }`}
                    >
                      {isHigh ? (
                        <AlertOctagon className="w-5 h-5 text-rose-600" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-amber-500" />
                      )}
                    </div>

                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <RiskBadge
                          category={alert.category}
                          status={alert.status}
                          score={alert.riskScore}
                          size="sm"
                        />
                        <span className="text-xs font-mono text-slate-400 font-medium">
                          {alert.id} • {formatDateTime(alert.detectedAt)}
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-slate-900 mt-1">{alert.title}</h4>
                      <p className="text-xs text-slate-500 mt-0.5 font-mono">
                        Rule: <span className="font-semibold text-slate-700">{alert.ruleBroken}</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-end lg:self-center">
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Target Amount</span>
                      <span className="font-bold text-slate-900 text-sm font-sans">
                        {formatCurrency(alert.amount)}
                      </span>
                    </div>

                    <button
                      type="button"
                      className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
                      aria-label="Expand alert details"
                    >
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details Section */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-2 border-t border-slate-100 text-xs space-y-4 animate-fade-in">
                    {/* Involved accounts */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Affected Account</span>
                        <span className="font-mono font-semibold text-slate-800">{alert.affectedAccount}</span>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Suspect Entity VPA</span>
                        <span className="font-mono font-semibold text-rose-600">{alert.suspectEntity}</span>
                      </div>
                    </div>

                    {/* Detailed Explanation */}
                    <div>
                      <h5 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-1">
                        Detailed Threat Narrative:
                      </h5>
                      <p className="text-slate-600 leading-relaxed bg-white p-3 rounded-xl border border-slate-200">
                        {alert.explanation}
                      </p>
                    </div>

                    {/* Indicators list */}
                    {alert.indicators && alert.indicators.length > 0 && (
                      <div>
                        <h5 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-1">
                          Corroborating Evidence:
                        </h5>
                        <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                          {alert.indicators.map((ind, i) => (
                            <li key={i}>{ind}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Recommended Safety Actions */}
                    <div>
                      <h5 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-1.5 text-blue-900">
                        Required Mitigation Protocols:
                      </h5>
                      <div className="space-y-1.5">
                        {alert.recommendedActions.map((act, i) => (
                          <div
                            key={i}
                            className="p-2.5 rounded-lg bg-blue-50/60 border border-blue-100 text-blue-900 flex items-center gap-2"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0" />
                            <span>{act}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Resolution action footer */}
                    {!isResolved && (
                      <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
                        <span className="text-[11px] text-slate-400">
                          Status: <strong className="text-amber-600">{alert.status}</strong>
                        </span>

                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => setResolveModalAlert(alert)}
                            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition flex items-center gap-1.5 shadow-sm"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Mark Resolved</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Resolve Incident Confirmation Modal */}
      {resolveModalAlert && (
        <ConfirmationModal
          isOpen={true}
          onClose={() => setResolveModalAlert(null)}
          onConfirm={handleResolveConfirm}
          isLoading={actionLoading}
          type="success"
          title={`Resolve Incident ${resolveModalAlert.id}`}
          confirmText="Confirm Resolution"
          cancelText="Cancel"
          message={
            <div>
              <p>
                Provide resolution notes for this incident report (
                <strong>{resolveModalAlert.title}</strong>):
              </p>
              <textarea
                rows={3}
                value={resolveNotes}
                onChange={(e) => setResolveNotes(e.target.value)}
                placeholder="e.g. Verified with user via callback; fraudulent VPA blacklisted at bank gateway."
                className="w-full mt-3 p-3 rounded-xl border border-slate-200 text-xs text-slate-800 outline-none focus:border-blue-500"
              />
            </div>
          }
        />
      )}
    </div>
  );
};

export default AlertsRiskReport;
