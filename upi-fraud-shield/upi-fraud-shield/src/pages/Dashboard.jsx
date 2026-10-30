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
  Layers
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
import { apiService } from "../services/apiService";
import { useApiMode } from "../hooks/useApiMode";
import { formatCurrency, formatDateTime } from "../utils/formatters";

export const Dashboard = () => {
  const navigate = useNavigate();
  const { mode } = useApiMode();

  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [dailyData, setDailyData] = useState([]);
  const [riskDist, setRiskDist] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [selectedTx, setSelectedTx] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, [mode]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [analyticsRes, txRes] = await Promise.all([
        apiService.getFraudAnalytics({}, mode),
        apiService.getTransactions({ status: "ALL" }, mode)
      ]);

      const analyticsData = analyticsRes.data || analyticsRes;
      setMetrics(analyticsData.metrics || {});
      setDailyData(analyticsData.dailyActivity || []);
      setRiskDist(analyticsData.riskDistribution || []);

      const transactions = txRes.data || [];
      setRecentTransactions(transactions.slice(0, 6));
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading fraud telemetry dashboard..." />;
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Welcome & Quick Actions Bar */}
      <div className="rounded-3xl bg-gradient-to-r from-navy-950 via-navy-900 to-navy-950 border border-navy-800 p-6 lg:p-8 text-white shadow-2xl relative overflow-hidden">
        {/* Background glow decoration */}
        <div className="absolute -right-20 -top-20 w-80 h-80 bg-blue-600/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute right-1/3 -bottom-20 w-60 h-60 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-400/30 text-cyan-300 text-xs font-semibold mb-3">
              <Zap className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span>Real-Time UPI Transaction Defense Node</span>
            </div>
            <h2 className="text-2xl lg:text-3xl font-extrabold tracking-tight text-white font-sans">
              UPI Fraud Detection Command Center
            </h2>
            <p className="mt-2 text-sm text-slate-300 leading-relaxed">
              Monitoring high-velocity transfers, reverse-debit collect traps, spoofed VPAs, and QR anomalies with real-time heuristic inference.
            </p>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => navigate("/analyze")}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-lg shadow-blue-600/30 transition flex items-center gap-2 group"
            >
              <Sparkles className="w-4 h-4 text-cyan-300 group-hover:rotate-12 transition" />
              <span>Analyze New UPI</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </button>

            <button
              onClick={() => navigate("/collect-requests")}
              className="px-4 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-bold transition flex items-center gap-2"
            >
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Collect Warnings</span>
            </button>

            <button
              onClick={() => navigate("/screenshot-scanner")}
              className="px-4 py-2.5 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700 text-xs font-bold transition flex items-center gap-2"
            >
              <FileScan className="w-4 h-4 text-cyan-400" />
              <span>Scan Screenshot</span>
            </button>
          </div>
        </div>
      </div>

      {/* 5 Core Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatsCard
          title="Total Transactions"
          value={metrics?.totalTransactions?.toLocaleString("en-IN") || "148,920"}
          change="+14.2%"
          isPositive={true}
          icon={Layers}
          variant="default"
        />

        <StatsCard
          title="Safe Transactions"
          value={metrics?.safeTransactions?.toLocaleString("en-IN") || "142,380"}
          subvalue="95.6% safe"
          change="+3.8%"
          isPositive={true}
          icon={ShieldCheck}
          variant="success"
        />

        <StatsCard
          title="Suspicious Flagged"
          value={metrics?.suspiciousTransactions?.toLocaleString("en-IN") || "4,890"}
          subvalue="Under review"
          change="-2.1%"
          isPositive={true}
          icon={AlertTriangle}
          variant="warning"
        />

        <StatsCard
          title="Blocked Transactions"
          value={metrics?.blockedTransactions?.toLocaleString("en-IN") || "1,650"}
          subvalue="Threat intercepted"
          change="+5.4%"
          isPositive={false}
          icon={Ban}
          variant="danger"
        />

        <StatsCard
          title="Total Fraud Prevented"
          value={metrics?.totalFraudPreventedAmount || "₹1,42,85,600"}
          subvalue="Direct savings"
          change="+18.5%"
          isPositive={true}
          icon={Activity}
          variant="navy"
        />
      </div>

      {/* Interactive Charts Section: Daily Activity & Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Daily Activity Graph (Recharts AreaChart) */}
        <div className="lg:col-span-2 rounded-2xl bg-white border border-slate-200/80 p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-900">Daily Transaction Activity & Threat Volumes</h3>
              <p className="text-xs text-slate-500">7-day volume breakdown across safe, suspicious, and blocked events</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                <span className="w-3 h-3 rounded bg-blue-600 inline-block" /> Safe
              </span>
              <span className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                <span className="w-3 h-3 rounded bg-amber-500 inline-block" /> Suspicious
              </span>
              <span className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                <span className="w-3 h-3 rounded bg-rose-500 inline-block" /> Blocked
              </span>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
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
                <Area type="monotone" dataKey="blockedVolume" name="Blocked Threat" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#blockGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Risk Distribution Pie / Donut Chart */}
        <div className="rounded-2xl bg-white border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Risk Score Distribution</h3>
            <p className="text-xs text-slate-500">Transaction classification based on heuristic AI threshold</p>
          </div>

          <div className="h-60 w-full my-2">
            <ResponsiveContainer width="100%" height="100%">
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
            </ResponsiveContainer>
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
            <h3 className="text-base font-bold text-slate-900">Recent UPI Transaction Stream</h3>
            <p className="text-xs text-slate-500">Live evaluation feed inspected by the risk engine</p>
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
                  {selectedTx.reasons.map((reason, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-slate-600">
                      <span className="text-rose-500 font-bold shrink-0">•</span>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-slate-400 text-[11px]">
                <span>Bank Ref: {selectedTx.bankRefNumber}</span>
                <span>Location: {selectedTx.location}</span>
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
