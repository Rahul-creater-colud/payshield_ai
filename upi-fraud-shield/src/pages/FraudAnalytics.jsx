import React, { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";
import {
  TrendingUp,
  Filter,
  Calendar,
  Layers,
  PieChart as PieIcon,
  BarChart2,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Download,
  RefreshCw
} from "lucide-react";
import LoadingSpinner from "../components/LoadingSpinner";
import { DataNotice, MetricCard } from "../components/PagePrimitives";
import { apiService } from "../services/apiService";
import { useApiMode } from "../hooks/useApiMode";
import { useToast } from "../hooks/useToast";

export const FraudAnalytics = () => {
  const { mode } = useApiMode();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [error, setError] = useState("");

  // Filters state
  const [selectedDateRange, setSelectedDateRange] = useState("7D"); // 24H, 7D, 30D
  const [selectedTxnType, setSelectedTxnType] = useState("ALL"); // ALL, P2P, P2M, COLLECT_REQUEST, QR_SCAN

  useEffect(() => {
    fetchAnalytics();
  }, [mode, selectedDateRange, selectedTxnType]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiService.getFraudAnalytics(
        { dateRange: selectedDateRange, txnType: selectedTxnType },
        mode
      );
      const data = res.data || res;
      if (!data.metrics || !Array.isArray(data.dailyActivity) ||
          !Array.isArray(data.riskDistribution) || !Array.isArray(data.transactionTypes)) {
        throw new Error("The backend returned an invalid analytics response.");
      }
      setAnalyticsData(data);
    } catch (err) {
      setAnalyticsData(null);
      setError(err.message || "Failed to load analytics data.");
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = () => {
    const jsonStr = JSON.stringify(analyticsData, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `upi-fraud-analytics-${selectedDateRange}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("Analytics response exported to JSON", "Export Complete");
  };

  if (loading) {
    return <LoadingSpinner message="Loading stored transaction analytics..." />;
  }

  if (error || !analyticsData) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-white p-8 text-center shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">Analytics unavailable</h2>
        <p className="mt-2 text-sm text-slate-600">{error || "No verified backend response is available."}</p>
        <button
          type="button"
          onClick={fetchAnalytics}
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
        >
          <RefreshCw className="h-4 w-4" /> Retry
        </button>
      </div>
    );
  }

  const {
    dailyActivity = [],
    riskDistribution = [],
    transactionTypes = [],
    metrics = {}
  } = analyticsData;
  const assessedCount = metrics.assessedTransactions || 0;
  const peakDay = dailyActivity.reduce(
    (peak, item) => item.totalVolume > (peak?.totalVolume || 0) ? item : peak,
    null
  );
  const riskScoreData = riskDistribution.map((item) => ({
    name: item.range,
    value: item.count,
    color: item.color
  }));
  const totalStopReview = dailyActivity.reduce((sum, item) => sum + item.stopReviewVolume, 0);
  const highScoreAssessments = riskDistribution
    .filter((item) => item.range.startsWith("81"))
    .reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* Header and Filter Control Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200/90 shadow-sm">
        <div>
          <h2 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
            Fraud Analytics & Model Status
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Synthetic telemetry, entity tracking, and model evaluation from the local prototype.
          </p>
          <p className="mt-1 text-[11px] font-semibold text-amber-700">
            {mode === "MOCK" ? "DEMO DATA — explicit mock mode" : analyticsData.data_label || "Local dataset"}
            {" • "}Rule-based heuristics; no validated ML benchmark or payment-provider connection
          </p>
          {analyticsData.updated_at && (
            <p className="mt-1 text-[11px] text-slate-400">
              Response updated: {new Date(analyticsData.updated_at).toLocaleString()}
            </p>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Date range filter */}
          <div className="flex items-center rounded-xl bg-slate-100 p-1 border border-slate-200 text-xs font-semibold">
            {["24H", "7D", "30D"].map((range) => (
              <button
                key={range}
                onClick={() => setSelectedDateRange(range)}
                className={`px-3 py-1.5 rounded-lg transition ${
                  selectedDateRange === range
                    ? "bg-white text-blue-600 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {range}
              </button>
            ))}
          </div>

          {/* Transaction type filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedTxnType}
              onChange={(e) => setSelectedTxnType(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 outline-none"
            >
              <option value="ALL">All Transaction Channels</option>
              <option value="P2P">Peer-to-Peer (P2P)</option>
              <option value="P2M">Merchant (P2M)</option>
              <option value="COLLECT_REQUEST">Collect Requests</option>
              <option value="QR_SCAN">QR Scans</option>
            </select>
          </div>

          {/* Export button */}
          <button
            onClick={handleExportData}
            className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition flex items-center gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard label="Transactions in local store" value={(metrics.totalTransactions || 0).toLocaleString("en-IN")} detail="Stored prototype records" icon={Layers} />
        <MetricCard label="Suspicious records" value={(metrics.suspiciousTransactions || 0).toLocaleString("en-IN")} detail="Medium/high heuristic classifications" icon={AlertTriangle} tone="amber" />
        <MetricCard label="High-score assessments" value={highScoreAssessments.toLocaleString("en-IN")} detail="Scores 81–100 in selected period" icon={ShieldAlert} tone="red" />
        <MetricCard label="Repeated suspicious entities" value="Not available" detail="No aggregate entity-frequency endpoint is configured" icon={PieIcon} tone="slate" />
        <MetricCard label="Fraud prevented" value="Not available" detail="No verified prevention events support this claim" icon={ShieldCheck} tone="slate" />
        <MetricCard label="Model evaluation" value="Not available" detail="No validated labeled benchmark is configured" icon={Zap} tone="slate" />
      </div>

      <DataNotice tone="warning">
        These visualizations summarize locally stored synthetic records and rule-based scores. They are not real-time UPI telemetry, validated model performance, or confirmed fraud categories.
      </DataNotice>

      {/* Row 1: Daily Fraud Detection & Transaction Volume (Dual Graphs) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Fraud Detection Line/Area Graph */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Daily Stop/Review Recommendations</h3>
              <p className="text-xs text-slate-500">High-risk internal recommendations; no payments are blocked</p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
              {totalStopReview.toLocaleString("en-IN")} in range
            </span>
          </div>

          <div className="h-72 w-full">
            {dailyActivity.length ? <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyActivity} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="fraudAmtGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="day" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val) => [`${Number(val).toLocaleString("en-IN")} recommendations`, "Stop/review"]}
                  contentStyle={{ backgroundColor: "#0f2038", borderRadius: "12px", border: "1px solid #1e3a5f", color: "#fff", fontSize: "12px" }}
                />
                <Area
                  type="monotone"
                  dataKey="stopReviewVolume"
                  stroke="#ef4444"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#fraudAmtGrad)"
                />
              </AreaChart>
            </ResponsiveContainer> : <div className="flex h-full items-center justify-center text-sm text-slate-500">No transaction activity in this range.</div>}
          </div>
        </div>

        {/* Transaction Volume Breakdown Graph */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Total Transaction Volume Trends</h3>
              <p className="text-xs text-slate-500">Stored transaction records versus recorded risk classifications</p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
              {peakDay ? `Peak: ${peakDay.day}` : "No recorded activity"}
            </span>
          </div>

          <div className="h-72 w-full">
            {dailyActivity.length ? <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyActivity} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="day" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val, name) => [`${val.toLocaleString()} txns`, name]}
                  contentStyle={{ backgroundColor: "#0f2038", borderRadius: "12px", border: "1px solid #1e3a5f", color: "#fff", fontSize: "12px" }}
                />
                <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
                <Bar dataKey="safeVolume" name="Safe Transactions" fill="#2563eb" radius={[4, 4, 0, 0]} />
                <Bar dataKey="suspiciousVolume" name="Suspicious Flagged" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer> : <div className="flex h-full items-center justify-center text-sm text-slate-500">No transaction activity in this range.</div>}
          </div>
        </div>
      </div>

      {/* Row 2: Safe vs Suspicious Pie Chart & Risk Score Distribution Bar Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Pie Chart: Risk Score Distribution */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/90 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Risk Score Distribution</h3>
            <p className="text-xs text-slate-500">Stored assessments by recorded score range</p>
          </div>

          <div className="h-64 w-full my-3">
            {assessedCount > 0 ? <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskScoreData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={95}
                  paddingAngle={4}
                  dataKey="value"
                  nameKey="name"
                >
                  {riskScoreData.map((entry, index) => (
                    <Cell key={`slice-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val, name) => [`${val.toLocaleString()} transactions`, name]}
                  contentStyle={{ backgroundColor: "#0f2038", borderRadius: "12px", border: "1px solid #1e3a5f", color: "#fff", fontSize: "12px" }}
                />
              </PieChart>
            </ResponsiveContainer> : <div className="flex h-full items-center justify-center text-sm text-slate-500">No risk assessments in this range.</div>}
          </div>

          <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100 text-center">
            {riskScoreData.slice(0, 3).map((item, idx) => (
              <div key={idx} className="p-2 rounded-xl bg-slate-50 border border-slate-100">
                <span className="block text-[10px] font-bold uppercase text-slate-500 truncate">{item.name}</span>
                <span className="text-xs font-extrabold text-slate-900 mt-0.5 block">{item.value.toLocaleString("en-IN")}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Distribution Chart (Bar by severity tier) */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200/90 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Fraud Risk Score Distribution (0 - 100)</h3>
              <p className="text-xs text-slate-500">Recorded assessment count clustered by score range</p>
            </div>
            <span className="text-xs font-semibold text-slate-400">Assessed: {assessedCount.toLocaleString("en-IN")}</span>
          </div>

          <div className="h-64 w-full">
            {assessedCount > 0 ? <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskDistribution} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis dataKey="range" type="category" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val) => [`${val.toLocaleString()} transactions`, "Volume"]}
                  contentStyle={{ backgroundColor: "#0f2038", borderRadius: "12px", border: "1px solid #1e3a5f", color: "#fff", fontSize: "12px" }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                  {riskDistribution.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer> : <div className="flex h-full items-center justify-center text-sm text-slate-500">No risk assessments in this range.</div>}
          </div>

          <div className="mt-4 p-3 rounded-xl bg-blue-50/60 border border-blue-100 text-xs text-blue-900 flex items-center gap-2">
            <Zap className="w-4 h-4 text-blue-600 shrink-0" />
            <span>
              Risk scores are heuristic recommendations, not proof of fraud. No validated model accuracy or external payment blocking is available.
            </span>
          </div>
        </div>
      </div>

      {/* Row 3: Channel Breakdown Table */}
      <div className="bg-white rounded-3xl border border-slate-200/90 p-6 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 mb-1">UPI Channels & Fraud Vulnerability Index</h3>
        <p className="text-xs text-slate-500 mb-4">Breakdown by payment initiation modality</p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-bold uppercase tracking-wider">
                <th className="py-3 px-4">UPI Channel Type</th>
                <th className="py-3 px-4">Total Audited</th>
                <th className="py-3 px-4">Safe Volume</th>
                <th className="py-3 px-4">Suspicious Flagged</th>
                <th className="py-3 px-4">Stop/Review Recommendations</th>
                <th className="py-3 px-4">Assessed Risk Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {transactionTypes.map((t, idx) => {
                const fraudRate = t.assessed ? ((t.suspicious / t.assessed) * 100).toFixed(1) : null;
                const isHighRate = fraudRate !== null && parseFloat(fraudRate) > 10;

                return (
                  <tr key={idx} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 px-4 font-bold text-slate-800">{t.type}</td>
                    <td className="py-3 px-4 font-mono">{t.total.toLocaleString()}</td>
                    <td className="py-3 px-4 text-emerald-600 font-mono">{t.safe.toLocaleString()}</td>
                    <td className="py-3 px-4 text-amber-600 font-mono">{t.suspicious.toLocaleString()}</td>
                    <td className="py-3 px-4 text-rose-600 font-mono">{t.stopReview.toLocaleString()}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full font-bold text-xs ${
                          isHighRate
                            ? "bg-rose-100 text-rose-700 border border-rose-200"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {fraudRate === null ? "N/A" : `${fraudRate}%`}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {!transactionTypes.length && (
                <tr>
                  <td colSpan="6" className="py-5 text-center text-slate-500">No transaction records in this range.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FraudAnalytics;
