import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  Eye,
  Download,
  ShieldCheck,
  AlertTriangle,
  Ban,
  Clock,
  ArrowUpDown,
  RefreshCw,
  X
} from "lucide-react";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import { apiService } from "../services/apiService";
import { useApiMode } from "../hooks/useApiMode";
import { useToast } from "../hooks/useToast";
import { formatCurrency, formatDateTime } from "../utils/formatters";

export const TransactionHistory = () => {
  const { mode } = useApiMode();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [transactions, setTransactions] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selectedTx, setSelectedTx] = useState(null);

  useEffect(() => {
    fetchTransactions();
  }, [mode, statusFilter]);

  const fetchTransactions = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiService.getTransactions(
        { search: searchTerm, status: statusFilter },
        mode
      );
      if (!Array.isArray(res.data)) {
        throw new Error("The backend returned an invalid transaction response.");
      }
      setTransactions(res.data);
    } catch (err) {
      setTransactions([]);
      setError(err.message || "Failed to fetch transaction records.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTransactions();
  };

  const filteredTransactions = transactions.filter((t) => {
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase();
    return (
      t.transactionId.toLowerCase().includes(q) ||
      t.senderUpi.toLowerCase().includes(q) ||
      t.receiverUpi.toLowerCase().includes(q) ||
      t.senderName.toLowerCase().includes(q) ||
      t.receiverName.toLowerCase().includes(q)
    );
  });

  const exportCSV = () => {
    if (filteredTransactions.length === 0) {
      toast.warning("No transactions to export", "Empty");
      return;
    }
    const headers = ["Transaction ID", "Sender Name", "Sender UPI", "Receiver Name", "Receiver UPI", "Amount", "Type", "Status", "Risk Score", "Timestamp"];
    const rows = filteredTransactions.map(t => [
      t.transactionId,
      t.senderName,
      t.senderUpi,
      t.receiverName,
      t.receiverUpi,
      t.amount,
      t.type,
      t.status,
      t.riskScore,
      t.timestamp
    ]);
    const csvContent = [headers.join(","), ...rows.map(r => r.map(c => `"${c}"`).join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `upi-transactions-audit-${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("Transaction audit log exported to CSV", "Exported");
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
            PayShield Transaction History
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Stored local input and analysis records; this is not a payment-provider ledger.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={exportCSV}
            className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-xs transition flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={fetchTransactions}
            className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 shadow-xs transition"
            title="Refresh Table"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Txn ID, VPA, or Name..."
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 bg-slate-50/50 text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:border-blue-500 outline-none transition font-medium"
          />
        </form>

        {/* Status Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-slate-400 mr-1 hidden lg:inline">Filter Status:</span>
          {["ALL", "SAFE", "FLAGGED", "STOP_RECOMMENDED", "UNASSESSED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition border ${
                statusFilter === st
                  ? st === "FLAGGED"
                    ? "bg-amber-500 text-white border-amber-500 shadow-sm"
                    : st === "STOP_RECOMMENDED"
                    ? "bg-rose-600 text-white border-rose-600 shadow-sm"
                    : st === "UNASSESSED"
                    ? "bg-slate-700 text-white border-slate-700 shadow-sm"
                    : st === "SAFE"
                    ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                    : "bg-slate-900 text-white border-slate-900 shadow-sm"
                  : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
              }`}
            >
              {st === "STOP_RECOMMENDED" ? "STOP / REVIEW" : st}
            </button>
          ))}
        </div>
      </div>

      {/* Transactions Table Container */}
      {loading ? (
        <LoadingSpinner message="Querying transaction records..." />
      ) : error ? (
        <div className="rounded-2xl border border-rose-200 bg-white p-8 text-center shadow-sm">
          <h3 className="text-base font-bold text-slate-900">Transaction records unavailable</h3>
          <p className="mt-2 text-sm text-slate-600">{error}</p>
          <button
            type="button"
            onClick={fetchTransactions}
            className="mt-4 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
          >
            Retry
          </button>
        </div>
      ) : filteredTransactions.length === 0 ? (
        <EmptyState
          title={transactions.length ? "No Transactions Match Filters" : "No transaction data available yet"}
          description={transactions.length
            ? `No transactions found matching "${searchTerm || statusFilter}". Try adjusting your search query or filters.`
            : "No transaction records are stored in the local database yet."}
          actionText="Clear Filters"
          onAction={() => {
            setSearchTerm("");
            setStatusFilter("ALL");
          }}
        />
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/80 text-slate-500 font-bold uppercase tracking-wider">
                  <th className="py-3.5 px-6">Transaction ID</th>
                  <th className="py-3.5 px-6">Sender Details</th>
                  <th className="py-3.5 px-6">Receiver Details</th>
                  <th className="py-3.5 px-6">Amount</th>
                  <th className="py-3.5 px-6">Timestamp</th>
                  <th className="py-3.5 px-6">Status & Score</th>
                  <th className="py-3.5 px-6 text-right">Forensics</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredTransactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50/70 transition group">
                    <td className="py-3.5 px-6 font-mono text-slate-800 font-semibold">
                      {tx.transactionId}
                      <span className="block text-[10px] text-slate-400 font-sans font-normal mt-0.5">
                        {tx.type}
                      </span>
                    </td>
                    <td className="py-3.5 px-6">
                      <div className="font-bold text-slate-900">{tx.senderName}</div>
                      <div className="text-[11px] font-mono text-slate-500">{tx.senderUpi}</div>
                    </td>
                    <td className="py-3.5 px-6">
                      <div className="font-bold text-slate-900">{tx.receiverName}</div>
                      <div className="text-[11px] font-mono text-slate-500">{tx.receiverUpi}</div>
                    </td>
                    <td className="py-3.5 px-6 font-bold text-slate-900 text-sm font-sans">
                      {formatCurrency(tx.amount)}
                    </td>
                    <td className="py-3.5 px-6 text-slate-500">
                      {formatDateTime(tx.timestamp)}
                    </td>
                    <td className="py-3.5 px-6">
                      <RiskBadge
                        category={tx.riskCategory}
                        status={tx.status}
                        score={tx.riskScore}
                        size="sm"
                      />
                    </td>
                    <td className="py-3.5 px-6 text-right">
                      <button
                        onClick={() => setSelectedTx(tx)}
                        className="px-3 py-1.5 rounded-xl border border-slate-200 text-slate-700 bg-white hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 font-semibold text-xs transition inline-flex items-center gap-1.5 shadow-xs"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Table Footer Summary */}
          <div className="py-3.5 px-6 bg-slate-50/70 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <span>Showing {filteredTransactions.length} transaction entries</span>
            <span>Local database records • no provider ledger</span>
          </div>
        </div>
      )}

      {/* Forensic Details Modal */}
      {selectedTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-xl bg-white rounded-3xl border border-slate-200 shadow-2xl p-6 lg:p-8 overflow-hidden">
            {/* Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-900">Payment Security Dossier</h3>
                  <RiskBadge
                    category={selectedTx.riskCategory}
                    status={selectedTx.status}
                    score={selectedTx.riskScore}
                    size="sm"
                  />
                </div>
                <p className="text-xs font-mono text-slate-400 mt-1">{selectedTx.transactionId}</p>
              </div>
              <button
                onClick={() => setSelectedTx(null)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="py-5 space-y-4 text-xs">
              {/* Counterparties */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Sender Party</span>
                  <span className="font-bold text-slate-900 text-sm block">{selectedTx.senderName}</span>
                  <span className="text-slate-500 font-mono text-[11px]">{selectedTx.senderUpi}</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Receiver Counterparty</span>
                  <span className="font-bold text-slate-900 text-sm block">{selectedTx.receiverName}</span>
                  <span className="text-slate-500 font-mono text-[11px]">{selectedTx.receiverUpi}</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Total Amount</span>
                  <span className="font-extrabold text-slate-900 text-base">{formatCurrency(selectedTx.amount)}</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Transaction Type</span>
                  <span className="font-semibold text-slate-800">{selectedTx.type}</span>
                </div>
              </div>

              {/* Recorded heuristic reasons */}
              <div>
                <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-2.5">
                  Recorded Heuristic Assessment:
                </h4>
                <div className="space-y-2">
                  {(selectedTx.reasons || []).map((r, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-slate-700 flex items-start gap-2.5 leading-relaxed"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 shrink-0" />
                      <span>{r}</span>
                    </div>
                  ))}
                  {!selectedTx.reasons?.length && (
                    <p className="text-slate-500">No risk assessment recorded for this transaction.</p>
                  )}
                </div>
              </div>

              {/* Extra Metadata */}
              <div className="grid grid-cols-2 gap-2 pt-2 text-[11px] text-slate-500 border-t border-slate-100">
                <div>
                  <span className="text-slate-400 block">Payment-provider reference:</span>
                  <span className="font-medium text-slate-700">No payment-provider reference</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Data source:</span>
                  <span className="font-medium text-slate-700">{selectedTx.data_label || "Stored local record"}</span>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setSelectedTx(null)}
                className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition"
              >
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransactionHistory;
