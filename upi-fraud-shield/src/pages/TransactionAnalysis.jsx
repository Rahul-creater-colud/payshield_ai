import React, { useState } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Sparkles,
  RefreshCw,
  Info,
  CheckCircle2,
  Clock,
  ArrowRight,
  Zap,
  HelpCircle,
  FileCheck2
} from "lucide-react";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import { apiService } from "../services/apiService";
import { useApiMode } from "../hooks/useApiMode";
import { useToast } from "../hooks/useToast";
import { validateTransactionForm } from "../utils/validators";
import { formatCurrency, formatDateTime } from "../utils/formatters";

const createDemoTransactionId = (prefix = "TEST") =>
  `${prefix}-${crypto.randomUUID().slice(0, 8).toUpperCase()}`;

export const TransactionAnalysis = () => {
  const { mode } = useApiMode();
  const toast = useToast();

  const [formData, setFormData] = useState({
    transactionId: "",
    senderUpi: "",
    receiverUpi: "",
    amount: "",
    transactionTime: new Date().toISOString().slice(0, 16),
    transactionType: "P2P"
  });

  const [errors, setErrors] = useState({});
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

  const presets = [
    {
      label: "Phishing Collect Trap",
      type: "HIGH",
      data: {
        transactionId: createDemoTransactionId("DEMO-PHISH"),
        senderUpi: "vikram.sharma@okhdfcbank",
        receiverUpi: "sbi-kyc-update-desk@ybl",
        amount: "24999",
        transactionTime: new Date().toISOString().slice(0, 16),
        transactionType: "COLLECT_REQUEST"
      }
    },
    {
      label: "Nocturnal Crypto Mule Spike",
      type: "HIGH",
      data: {
        transactionId: createDemoTransactionId("DEMO-MULE"),
        senderUpi: "ananya.sen@ybl",
        receiverUpi: "fastpay.crypto99@airtel",
        amount: "45000",
        transactionTime: "2026-10-30T02:35",
        transactionType: "P2P"
      }
    },
    {
      label: "Infant Merchant QR Anomaly",
      type: "MEDIUM",
      data: {
        transactionId: createDemoTransactionId("DEMO-QR"),
        senderUpi: "rohan.d@oksbi",
        receiverUpi: "metro.gadgets@razorpay",
        amount: "18400",
        transactionTime: new Date().toISOString().slice(0, 16),
        transactionType: "QR_SCAN"
      }
    },
    {
      label: "Legitimate Food Delivery",
      type: "LOW",
      data: {
        transactionId: createDemoTransactionId("DEMO-SAFE"),
        senderUpi: "sneha.reddy@okicici",
        receiverUpi: "swiggy.pay@icici",
        amount: "480",
        transactionTime: new Date().toISOString().slice(0, 16),
        transactionType: "P2M"
      }
    }
  ];

  const handleApplyPreset = (preset) => {
    setFormData(preset.data);
    setErrors({});
    setResult(null);
    toast.info(`Loaded test scenario: "${preset.label}"`, "Preset Applied");
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const validation = validateTransactionForm(formData);
    if (!validation.isValid) {
      setErrors(validation.errors);
      toast.error("Please correct the form errors before analyzing", "Validation Failed");
      return;
    }

    setAnalyzing(true);
    setResult(null);

    try {
      const response = await apiService.analyzeTransaction(formData, mode);
      const data = response.data || response;
      setResult({
        ...data,
        data_label: data.data_label || (mode === "MOCK" ? "DEMO DATA" : "DEMO / SYNTHETIC DATA")
      });

      if (data.riskCategory === "HIGH") {
        toast.error(`High-risk recommendation: ${data.riskScore}/100. No payment was blocked or executed.`, "Review Recommended");
      } else if (data.riskCategory === "MEDIUM") {
        toast.warning(`Moderate Risk: Score ${data.riskScore}/100. Caution advised before proceeding.`, "Suspicious Activity");
      } else {
        toast.success(`Low heuristic risk: ${data.riskScore}/100. No payment was executed.`, "Assessment Complete");
      }
    } catch (err) {
      console.error("Analysis failed:", err);
      toast.error(err.message || "Failed to analyze transaction", "Engine Error");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setFormData({
      transactionId: "",
      senderUpi: "",
      receiverUpi: "",
      amount: "",
      transactionTime: new Date().toISOString().slice(0, 16),
      transactionType: "P2P"
    });
    setErrors({});
    setResult(null);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
            Local UPI Transaction Risk Analyzer
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Submit transaction details for local rule-based analysis. No UPI network, NPCI registry, or payment provider is connected.
          </p>
          <p className="mt-1 text-[11px] font-semibold text-amber-700">
            Analysis-only prototype • records and preset scenarios are demo/synthetic data • no payment is executed or blocked
          </p>
        </div>

        {/* Preset quick buttons */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-semibold text-slate-400 mr-1 hidden md:inline">Presets:</span>
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleApplyPreset(p)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold transition border ${
                p.type === "HIGH"
                  ? "bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100"
                  : p.type === "MEDIUM"
                  ? "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100"
                  : "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Form on Left/Top, Result on Right/Bottom */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Form Container */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200/90 p-6 lg:p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* UPI Transaction ID */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  PayShield Test/Reference ID <span className="text-rose-500">*</span>
                </label>
                <button
                  type="button"
                  onClick={() =>
                    setFormData((prev) => ({
                      ...prev,
                      transactionId: createDemoTransactionId()
                    }))
                  }
                  className="text-[11px] font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Auto-Generate
                </button>
              </div>
              <input
                type="text"
                name="transactionId"
                value={formData.transactionId}
                onChange={handleInputChange}
                placeholder="e.g. TEST-2026-TRANSACTION-01"
                className={`w-full px-4 py-2.5 rounded-xl border font-mono text-xs transition outline-none ${
                  errors.transactionId
                    ? "border-rose-300 bg-rose-50/30 text-rose-900 focus:border-rose-500"
                    : "border-slate-200 bg-slate-50/50 text-slate-800 focus:border-blue-500 focus:bg-white"
                }`}
              />
              {errors.transactionId && (
                <p className="text-[11px] text-rose-500 mt-1">{errors.transactionId}</p>
              )}
            </div>

            {/* Sender and Receiver UPI IDs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Sender UPI ID (VPA) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  name="senderUpi"
                  value={formData.senderUpi}
                  onChange={handleInputChange}
                  placeholder="e.g. sender@okaxis"
                  className={`w-full px-4 py-2.5 rounded-xl border font-mono text-xs transition outline-none ${
                    errors.senderUpi
                      ? "border-rose-300 bg-rose-50/30 text-rose-900 focus:border-rose-500"
                      : "border-slate-200 bg-slate-50/50 text-slate-800 focus:border-blue-500 focus:bg-white"
                  }`}
                />
                {errors.senderUpi && (
                  <p className="text-[11px] text-rose-500 mt-1">{errors.senderUpi}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Receiver UPI ID (VPA) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  name="receiverUpi"
                  value={formData.receiverUpi}
                  onChange={handleInputChange}
                  placeholder="e.g. payee@okhdfcbank"
                  className={`w-full px-4 py-2.5 rounded-xl border font-mono text-xs transition outline-none ${
                    errors.receiverUpi
                      ? "border-rose-300 bg-rose-50/30 text-rose-900 focus:border-rose-500"
                      : "border-slate-200 bg-slate-50/50 text-slate-800 focus:border-blue-500 focus:bg-white"
                  }`}
                />
                {errors.receiverUpi && (
                  <p className="text-[11px] text-rose-500 mt-1">{errors.receiverUpi}</p>
                )}
              </div>
            </div>

            {/* Amount and Transaction Type */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Transfer Amount (₹) <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 font-bold text-slate-400 text-xs">
                    ₹
                  </span>
                  <input
                    type="number"
                    step="0.01"
                    name="amount"
                    value={formData.amount}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    className={`w-full pl-8 pr-4 py-2.5 rounded-xl border font-semibold text-xs transition outline-none ${
                      errors.amount
                        ? "border-rose-300 bg-rose-50/30 text-rose-900 focus:border-rose-500"
                        : "border-slate-200 bg-slate-50/50 text-slate-800 focus:border-blue-500 focus:bg-white"
                    }`}
                  />
                </div>
                {errors.amount && (
                  <p className="text-[11px] text-rose-500 mt-1">{errors.amount}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Transaction Type <span className="text-rose-500">*</span>
                </label>
                <select
                  name="transactionType"
                  value={formData.transactionType}
                  onChange={handleInputChange}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 text-xs font-medium focus:border-blue-500 focus:bg-white outline-none transition"
                >
                  <option value="P2P">Peer-to-Peer (P2P)</option>
                  <option value="COLLECT_REQUEST">Collect Request (Reverse Debit)</option>
                  <option value="QR_SCAN">Dynamic / Static QR Scan</option>
                  <option value="P2M">Person to Merchant (P2M)</option>
                  <option value="BILL_PAY">Bharat BillPay (BBPS)</option>
                </select>
                {errors.transactionType && (
                  <p className="text-[11px] text-rose-500 mt-1">{errors.transactionType}</p>
                )}
              </div>
            </div>

            {/* Transaction Time */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Transaction Initiation Timestamp
              </label>
              <input
                type="datetime-local"
                name="transactionTime"
                value={formData.transactionTime}
                onChange={handleInputChange}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-800 text-xs font-medium focus:border-blue-500 focus:bg-white outline-none transition"
              />
              <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
                <Info className="w-3 h-3 inline text-slate-400" />
                Nocturnal transfers (11 PM - 5 AM) receive elevated scrutiny from velocity anomaly filters.
              </p>
            </div>

            {/* Action buttons */}
            <div className="pt-4 flex items-center gap-3">
              <button
                type="submit"
                disabled={analyzing}
                className="flex-1 py-3 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-blue-600/30 transition flex items-center justify-center gap-2 group disabled:opacity-60"
              >
                {analyzing ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Checking local rules...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-cyan-300 group-hover:rotate-12 transition" />
                    <span>Analyze Test Transaction</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleReset}
                disabled={analyzing}
                className="px-4 py-3 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-100 font-semibold text-xs transition"
              >
                Reset
              </button>
            </div>
          </form>
        </div>

        {/* Results / Risk Output Panel */}
        <div className="lg:col-span-5">
          {analyzing ? (
            <div className="bg-white rounded-3xl border border-slate-200/90 p-8 shadow-sm">
              <LoadingSpinner
                message="Local Heuristic Rules Evaluating..."
                subtext="Checking submitted fields against configured local rules; no external registry or payment service is contacted"
              />
            </div>
          ) : result ? (
            <div
              className={`rounded-3xl border p-6 lg:p-7 shadow-lg transition-all animate-fade-in ${
                result.riskCategory === "HIGH"
                  ? "bg-gradient-to-b from-rose-950/20 via-white to-white border-rose-500/30 shadow-rose-500/10"
                  : result.riskCategory === "MEDIUM"
                  ? "bg-gradient-to-b from-amber-950/20 via-white to-white border-amber-500/30 shadow-amber-500/10"
                  : "bg-gradient-to-b from-emerald-950/20 via-white to-white border-emerald-500/30 shadow-emerald-500/10"
              }`}
            >
              {/* Header Status */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Analysis Assessment • {result.data_label}
                  </span>
                  <div className="mt-1 flex items-center gap-2">
                    <RiskBadge
                      category={result.riskCategory}
                      status={result.status}
                      score={result.riskScore}
                      size="lg"
                    />
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Engine Verdict</span>
                  <p
                    className={`text-sm font-extrabold ${
                      result.riskCategory === "HIGH"
                        ? "text-rose-600"
                        : result.riskCategory === "MEDIUM"
                        ? "text-amber-600"
                        : "text-emerald-600"
                    }`}
                  >
                    {result.status}
                  </p>
                </div>
              </div>

              {/* Risk Gauge Bar */}
              <div className="my-5 p-4 rounded-2xl bg-slate-50 border border-slate-200/80">
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-semibold text-slate-700">Risk Severity Score:</span>
                  <span className="font-mono font-bold text-slate-900 text-sm">
                    {result.riskScore} / 100
                  </span>
                </div>
                <div className="h-2.5 w-full bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      result.riskCategory === "HIGH"
                        ? "bg-rose-500"
                        : result.riskCategory === "MEDIUM"
                        ? "bg-amber-400"
                        : "bg-emerald-500"
                    }`}
                    style={{ width: `${result.riskScore}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-mono">
                  <span>0 (Safe)</span>
                  <span>35 (Caution)</span>
                  <span>70 (Critical)</span>
                  <span>100</span>
                </div>
              </div>

              {/* Transaction Key Points */}
              <div className="grid grid-cols-2 gap-3 text-xs p-3.5 rounded-xl bg-slate-50/80 border border-slate-100 mb-5">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Amount</span>
                  <span className="font-bold text-slate-800">{formatCurrency(result.amount)}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Type</span>
                  <span className="font-semibold text-slate-700">{result.type}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Receiver VPA</span>
                  <span className="font-mono text-slate-800 break-all">{result.receiverUpi}</span>
                </div>
              </div>

              {/* Flagged Reasons / Explanations */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                  <FileCheck2 className="w-4 h-4 text-blue-600" /> Flagged Reasons & Detection Triggers:
                </h4>

                <div className="space-y-2">
                  {result.reasons && result.reasons.length > 0 ? (
                    result.reasons.map((r, i) => (
                      <div
                        key={i}
                        className={`p-3 rounded-xl border text-xs leading-relaxed flex items-start gap-2.5 ${
                          result.riskCategory === "HIGH"
                            ? "bg-rose-50/60 border-rose-200/80 text-rose-900"
                            : result.riskCategory === "MEDIUM"
                            ? "bg-amber-50/60 border-amber-200/80 text-amber-900"
                            : "bg-emerald-50/60 border-emerald-200/80 text-emerald-900"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                            result.riskCategory === "HIGH"
                              ? "bg-rose-600"
                              : result.riskCategory === "MEDIUM"
                              ? "bg-amber-500"
                              : "bg-emerald-600"
                          }`}
                        />
                        <span>{r}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500">No anomaly triggers detected.</p>
                  )}
                </div>
              </div>

              {/* Recommendation Footer */}
              <div className="mt-6 pt-4 border-t border-slate-100 text-xs">
                <span className="font-bold text-slate-700 block mb-1">Recommended Operator Action:</span>
                <p className="text-slate-600">
                  {result.riskCategory === "HIGH"
                    ? "Internal stop/review recommendation only. Verify independently with your payment provider; PayShield cannot stop this payment."
                    : result.riskCategory === "MEDIUM"
                    ? "Independent verification is recommended. PayShield does not enforce secondary verification."
                    : "No configured heuristic trigger matched. This is not a guarantee of safety or payment clearance."}
                </p>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-8 bg-white rounded-3xl border border-dashed border-slate-200 text-center text-slate-400">
              <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                <Sparkles className="w-6 h-6 text-blue-500" />
              </div>
              <h4 className="text-sm font-bold text-slate-800">Awaiting Transaction Parameters</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-xs leading-relaxed">
                Submit a test record or choose a demo preset to view a local heuristic score and its recorded rules.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TransactionAnalysis;
