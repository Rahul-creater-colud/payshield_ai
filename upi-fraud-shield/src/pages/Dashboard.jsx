import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ShieldCheck,
  AlertTriangle,
  Ban,
  Activity,
  ArrowRight,
  TrendingUp,
  Sparkles,
  FileScan,
  ShieldAlert,
  Zap,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  Layers,
  RefreshCw
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";
import StatsCard from "../components/StatsCard";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import { apiService } from "../services/apiService";
import { useApiMode } from "../hooks/useApiMode";
import { formatCurrency, formatDateTime } from "../utils/formatters";

export const Dashboard = () => {
  const navigate = useNavigate();
  const { mode, isBackendReachable } = useApiMode();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [metrics, setMetrics] = useState(null);
  const [dataLabel, setDataLabel] = useState("");
  const [dailyData, setDailyData] = useState([]);
  const [riskDist, setRiskDist] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [selectedTx, setSelectedTx] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, [mode]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError("");
    try {
      const [analyticsRes, txRes] = await Promise.all([
        apiService.getFraudAnalytics({ dateRange: "7D" }, mode),
        apiService.getTransactions({ status: "ALL" }, mode)
      ]);

      const analyticsData = analyticsRes.data || analyticsRes;
      const transactionData = txRes.data?.data || txRes.data;
      if (!Array.isArray(transactionData)) {
        throw new Error("The backend returned an invalid transaction response.");
      }
      if (!analyticsData.metrics || !Array.isArray(analyticsData.dailyActivity) ||
          !Array.isArray(analyticsData.riskDistribution)) {
        throw new Error("The backend returned an invalid dashboard statistics response.");
      }
      if (typeof analyticsData.updated_at !== "string" ||
          Number.isNaN(Date.parse(analyticsData.updated_at))) {
        throw new Error("The backend returned an invalid dashboard update timestamp.");
      }
      const requiredCounts = [
        "totalTransactions",
        "safeTransactions",
        "suspiciousTransactions",
        "blockedTransactions",
        "stopReviewRecommendations"
      ];
      if (requiredCounts.some((key) => !Number.isInteger(analyticsData.metrics[key]))) {
        throw new Error("The backend returned invalid dashboard statistics.");
      }
      setMetrics(analyticsData.metrics);
      setDataLabel(
        analyticsData.data_label ||
        (mode === "MOCK" ? "DEMO DATA" : "LOCAL PROTOTYPE RECORDS")
      );
      setDailyData(analyticsData.dailyActivity);
      setRiskDist(analyticsData.riskDistribution);

      const transactions = transactionData;
      setRecentTransactions(transactions.slice(0, 6));
      setLastUpdated(analyticsData.updated_at);
    } catch (err) {
      setMetrics(null);
      setDataLabel("");
      setDailyData([]);
      setRiskDist([]);
      setRecentTransactions([]);
      setError(err.message || "Unable to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading fraud telemetry dashboard..." />;
  }

  if (error || !metrics) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-white p-8 text-center shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">
          {mode === "MOCK"
            ? "Demo data unavailable"
            : isBackendReachable
              ? "Dashboard data unavailable"
              : "Backend disconnected"}
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          {error || "No verified dashboard response is available."}
        </p>
        <button
          type="button"
          onClick={loadDashboardData}
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
        >
          <RefreshCw className="h-4 w-4" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="surface-card p-5 sm:p-6">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-center">
          <div className="max-w-xl">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className={`inline-flex items-center gap-1.5 rounded border px-2 py-1 text-[10px] font-semibold ${isBackendReachable ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-rose-200 bg-rose-50 text-rose-800"}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${isBackendReachable ? "bg-emerald-500" : "bg-rose-500"}`} />
                {isBackendReachable ? "LOCAL SERVICE CONNECTED" : "API RESPONSE RECEIVED"}
              </span>
              <span className="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-[10px] font-semibold text-amber-800">
                {mode === "MOCK" ? "DEMO DATA" : dataLabel}
              </span>
            </div>
            <h2 className="text-xl font-semibold tracking-tight text-ink sm:text-2xl">
              Stored activity overview
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Local rule-based analysis of records submitted to this prototype. No NPCI or payment-provider connection is configured; PayShield cannot execute or block real payments.
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Last updated: {lastUpdated ? formatDateTime(lastUpdated) : "Not available"}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={loadDashboardData}
              className="inline-flex items-center gap-2 rounded-md border border-outline-soft bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-canvas"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => navigate("/analyze")}
              className="btn-primary"
            >
              <Sparkles className="h-4 w-4" />
              <span>Analyze test transaction</span>
            </button>
            <button
              onClick={() => navigate("/collect-requests")}
              className="inline-flex items-center gap-2 rounded-md border border-outline-soft bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-canvas"
            >
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <span>Collect requests</span>
            </button>
            <button
              onClick={() => navigate("/url-scanner")}
              className="inline-flex items-center gap-2 rounded-md border border-outline-soft bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-canvas"
            >
              <FileScan className="h-4 w-4 text-brand-teal" />
              <span>Scan URL</span>
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <StatsCard
          title="Stored Transactions"
          value={metrics.totalTransactions.toLocaleString("en-IN")}
          subvalue={`${metrics.assessedTransactions.toLocaleString("en-IN")} assessed by PayShield`}
          icon={Layers}
          variant="default"
        />

        <StatsCard
          title="Safe Transactions"
          value={metrics.safeTransactions.toLocaleString("en-IN")}
          subvalue="Recorded LOW-risk classifications"
          icon={ShieldCheck}
          variant="success"
        />

        <StatsCard
          title="Suspicious Flagged"
          value={metrics.suspiciousTransactions.toLocaleString("en-IN")}
          subvalue="Recorded medium/high risk classifications"
          icon={AlertTriangle}
          variant="warning"
        />

        <StatsCard
          title="Internal Stop / Review"
          value={metrics.stopReviewRecommendations.toLocaleString("en-IN")}
          subvalue="PayShield recommendations; payments not stopped"
          icon={Ban}
          variant="danger"
        />

        <StatsCard
          title="Verified Provider Blocks"
          value={metrics.blockedTransactions.toLocaleString("en-IN")}
          subvalue="Only verified non-simulated provider events"
          icon={Ban}
          variant="default"
        />

        <StatsCard
          title="Fraud Prevented"
          value={metrics.totalFraudPreventedAmount == null ? "Not available" : formatCurrency(metrics.totalFraudPreventedAmount)}
          subvalue="No verified prevention events"
          icon={Activity}
          variant="default"
        />
      </div>
      {metrics.totalTransactions === 0 && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
          No transaction data available yet. Statistics are zero until transactions are stored.
        </div>
      )}
      <p className="text-xs text-slate-500">
        {metrics.stopReviewRecommendations.toLocaleString("en-IN")} internal stop/review recommendations; these do not stop payments.
      </p>

      {/* Interactive Charts Section: Daily Activity & Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Daily Activity Graph (Recharts AreaChart) */}
        <div className="lg:col-span-2 rounded-2xl bg-white border border-slate-200/80 p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-900">Daily Transaction Activity & Threat Volumes</h3>
              <p className="text-xs text-slate-500">Stored transaction records by recorded assessment outcome (last 7 days)</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                <span className="w-3 h-3 rounded bg-blue-600 inline-block" /> Safe
              </span>
              <span className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                <span className="w-3 h-3 rounded bg-amber-500 inline-block" /> Suspicious
              </span>
              <span className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                <span className="w-3 h-3 rounded bg-rose-500 inline-block" /> Stop/review
              </span>
            </div>
          </div>

          <div className="h-72 w-full">
            {dailyData.length ? <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="safeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="suspGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="blockGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#64748b" }} stroke="#cbd5e1" />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} stroke="#cbd5e1" />
                <Tooltip
                  formatter={(val, name) => [`${Number(val).toLocaleString()} txns`, name]}
                  contentStyle={{ backgroundColor: "#0f2038", borderRadius: "12px", border: "1px solid #1e3a5f", color: "#fff", fontSize: "12px" }}
                />
                <Area type="monotone" dataKey="safeVolume" name="Safe Volume" stroke="#2563eb" strokeWidth={2} fillOpacity={1} fill="url(#safeGrad)" />
                <Area type="monotone" dataKey="suspiciousVolume" name="Suspicious" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#suspGrad)" />
                <Area type="monotone" dataKey="stopReviewVolume" name="Stop/review recommendations" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#blockGrad)" />
              </AreaChart>
            </ResponsiveContainer> : <EmptyState title="No transaction activity" description="No stored transactions fall within the selected 7-day chart window." />}
          </div>
        </div>

        {/* Right: Risk Distribution Pie / Donut Chart */}
        <div className="rounded-2xl bg-white border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Risk Score Distribution</h3>
            <p className="text-xs text-slate-500">Recorded rule-based assessments only</p>
          </div>

          <div className="h-60 w-full my-2">
            {riskDist.some((entry) => entry.count > 0) ? <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskDist}
                  dataKey="count"
                  nameKey="range"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                >
                  {riskDist.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val, name) => [`${Number(val).toLocaleString()} txns`, name]}
                  contentStyle={{ backgroundColor: "#0f2038", borderRadius: "12px", border: "1px solid #1e3a5f", color: "#fff", fontSize: "12px" }}
                />
              </PieChart>
            </ResponsiveContainer> : <EmptyState title="No risk assessments yet" description="Risk distribution appears after transaction records have an assessment." />}
          </div>

          <div className="space-y-1.5 pt-3 border-t border-slate-100">
            {riskDist.slice(0, 4).map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-slate-600">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  {item.range}
                </span>
                <span className="font-semibold text-slate-800">{item.percent}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Transactions Table */}
      <div className="rounded-2xl bg-white border border-slate-200/80 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
          <div>
            <h3 className="text-base font-bold text-slate-900">Recent PayShield Transaction Records</h3>
            <p className="text-xs text-slate-500">Stored local inputs; unassessed records are not presented as safe</p>
          </div>

          <button
            onClick={() => navigate("/history")}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 transition"
          >
            <span>View All Transaction History</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto -mx-6">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200/80 bg-slate-50/70 text-slate-500 font-semibold uppercase tracking-wider">
                <th className="py-3 px-6">Transaction ID</th>
                <th className="py-3 px-6">Sender UPI</th>
                <th className="py-3 px-6">Receiver UPI</th>
                <th className="py-3 px-6">Amount</th>
                <th className="py-3 px-6">Type</th>
                <th className="py-3 px-6">Status & Risk</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recentTransactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-slate-50/60 transition group">
                  <td className="py-3 px-6 font-mono font-medium text-slate-800">
                    {tx.transactionId}
                  </td>
                  <td className="py-3 px-6">
                    <div className="font-medium text-slate-800">{tx.senderName}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{tx.senderUpi}</div>
                  </td>
                  <td className="py-3 px-6">
                    <div className="font-medium text-slate-800">{tx.receiverName}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{tx.receiverUpi}</div>
                  </td>
                  <td className="py-3 px-6 font-semibold text-slate-900">
                    {formatCurrency(tx.amount)}
                  </td>
                  <td className="py-3 px-6">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                      {tx.type}
                    </span>
                  </td>
                  <td className="py-3 px-6">
                    <RiskBadge category={tx.riskCategory} status={tx.status} score={tx.riskScore} size="sm" />
                  </td>
                  <td className="py-3 px-6 text-right">
                    <button
                      onClick={() => setSelectedTx(tx)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition"
                      title="Inspect Transaction"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {!recentTransactions.length && (
                <tr>
                  <td colSpan="7" className="px-6 py-6 text-center text-sm text-slate-500">
                    No transaction data available yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transaction Details Modal */}
      {selectedTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-xl bg-white rounded-2xl border border-slate-200 shadow-2xl p-6 overflow-hidden">
            <div className="flex items-start justify-between pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-900">Transaction Forensic Details</h3>
                  <RiskBadge category={selectedTx.riskCategory} status={selectedTx.status} score={selectedTx.riskScore} size="sm" />
                </div>
                <p className="text-xs font-mono text-slate-500 mt-0.5">{selectedTx.transactionId}</p>
              </div>
              <button
                onClick={() => setSelectedTx(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                ✕
              </button>
            </div>

            <div className="py-4 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4 p-3 bg-slate-50 rounded-xl border border-slate-100">
                <div>
                  <span className="text-slate-400 block font-medium">Sender</span>
                  <span className="font-semibold text-slate-800">{selectedTx.senderName}</span>
                  <span className="text-slate-500 block font-mono text-[11px]">{selectedTx.senderUpi}</span>
                </div>
                <div>
                  <span className="text-slate-400 block font-medium">Receiver</span>
                  <span className="font-semibold text-slate-800">{selectedTx.receiverName}</span>
                  <span className="text-slate-500 block font-mono text-[11px]">{selectedTx.receiverUpi}</span>
                </div>
                <div>
                  <span className="text-slate-400 block font-medium">Amount</span>
                  <span className="text-sm font-bold text-slate-900">{formatCurrency(selectedTx.amount)}</span>
                </div>
                <div>
                  <span className="text-slate-400 block font-medium">Timestamp</span>
                  <span className="font-medium text-slate-700">{formatDateTime(selectedTx.timestamp)}</span>
                </div>
              </div>

              <div>
                <h4 className="font-bold text-slate-800 mb-2">Threat Evaluation Findings:</h4>
                <ul className="space-y-1.5">
                  {(selectedTx.reasons || []).map((reason, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-slate-600">
                      <span className="text-rose-500 font-bold shrink-0">•</span>
                      <span>{reason}</span>
                    </li>
                  ))}
                  {!selectedTx.reasons?.length && (
                    <li className="text-slate-500">No risk assessment recorded for this transaction.</li>
                  )}
                </ul>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-slate-400 text-[11px]">
                <span>No payment-provider reference (analysis only)</span>
                <span>{selectedTx.data_label || "Stored local record"}</span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setSelectedTx(null)}
                className="px-4 py-2 rounded-xl bg-slate-900 text-white font-semibold text-xs hover:bg-slate-800 transition"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
