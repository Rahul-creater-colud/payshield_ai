import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  AlertOctagon,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  HelpCircle,
  Info,
  DollarSign,
  ArrowRight,
  ShieldAlert,
  Ban,
  Check
} from "lucide-react";
import RiskBadge from "../components/RiskBadge";
import ConfirmationModal from "../components/ConfirmationModal";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import { apiService } from "../services/apiService";
import { useApiMode } from "../hooks/useApiMode";
import { useToast } from "../hooks/useToast";
import { formatCurrency, formatDateTime } from "../utils/formatters";

export const CollectRequestWarning = () => {
  const { mode } = useApiMode();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState([]);
  const [activeModal, setActiveModal] = useState(null); // { type: 'ACCEPT' | 'REJECT', request: item }
  const [actionLoading, setActionLoading] = useState(false);
  const [confirmStep, setConfirmStep] = useState(1);

  useEffect(() => {
    loadCollectRequests();
  }, [mode]);

  const loadCollectRequests = async () => {
    setLoading(true);
    try {
      const res = await apiService.getCollectRequests(mode);
      setRequests(res.data || []);
    } catch (err) {
      console.error("Error loading collect requests:", err);
      toast.error("Failed to load collect requests", "Network Error");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenActionModal = (request, type) => {
    setConfirmStep(1);
    setActiveModal({ type, request });
  };

  const handleConfirmAction = async () => {
    if (!activeModal) return;
    const { type, request } = activeModal;

    // If user is trying to ACCEPT a high risk request, force step 2 acknowledgment
    if (type === "ACCEPT" && request.riskCategory === "HIGH" && confirmStep === 1) {
      setConfirmStep(2);
      return;
    }

    setActionLoading(true);
    try {
      const res = await apiService.actionCollectRequest(request.id, type, mode);
      toast.success(
        res.message || `Request successfully ${type === "ACCEPT" ? "approved" : "rejected"}`,
        type === "ACCEPT" ? "Payment Authorized" : "Request Rejected & VPA Blocked"
      );
      setActiveModal(null);
      loadCollectRequests();
    } catch (err) {
      console.error("Action error:", err);
      toast.error(err.message || "Failed to process request action", "Error");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Inspecting pending UPI collect requests..." />;
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto animate-fade-in">
      {/* Critical Educational Alert Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-rose-950 via-rose-900 to-navy-950 border-2 border-rose-500/40 p-6 text-white shadow-xl relative overflow-hidden">
        <div className="flex items-start gap-4 relative z-10">
          <div className="p-3 rounded-2xl bg-rose-600/30 border border-rose-500/50 text-rose-300 shrink-0">
            <AlertOctagon className="w-8 h-8 text-rose-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-rose-500/30 text-rose-200 border border-rose-400/40">
                CRITICAL UPI SECURITY NOTICE
              </span>
            </div>
            <h3 className="text-lg lg:text-xl font-extrabold text-white mt-1">
              Never Enter Your UPI PIN to Receive Money or Claim Refunds!
            </h3>
            <p className="text-xs text-rose-200/90 mt-1.5 leading-relaxed max-w-3xl">
              A <strong>Collect Request</strong> asks you to transfer funds FROM your account to the requester.
              Fraudsters masquerade as customer care representatives, buyers on OLX, or lottery organizers to initiate reverse-debit requests.
              <strong> Approving any collect request will immediately DEBIT money from your bank balance!</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Screen Title & Summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
            Suspicious Collect Request Interception Shield
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Review incoming UPI debit pull requests analyzed by our threat intelligence heuristic engine.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold">
          <span className="px-3 py-1.5 rounded-xl bg-rose-50 text-rose-700 border border-rose-200">
            {requests.filter((r) => r.riskCategory === "HIGH" && r.status === "PENDING").length} High Risk
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-amber-50 text-amber-700 border border-amber-200">
            {requests.filter((r) => r.riskCategory === "MEDIUM" && r.status === "PENDING").length} Medium Risk
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200">
            {requests.filter((r) => r.riskCategory === "LOW" && r.status === "PENDING").length} Verified
          </span>
        </div>
      </div>

      {/* Requests List */}
      {requests.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="No Pending Collect Requests"
          description="Your UPI ID is safe. No inbound payment debit requests are currently awaiting authorization."
        />
      ) : (
        <div className="space-y-4">
          {requests.map((item) => {
            const isHighRisk = item.riskCategory === "HIGH";
            const isMediumRisk = item.riskCategory === "MEDIUM";
            const isPending = item.status === "PENDING";
            const isResolved = !isPending;

            return (
              <div
                key={item.id}
                className={`rounded-2xl border p-5 lg:p-6 transition-all duration-200 ${
                  isHighRisk && isPending
                    ? "bg-white border-rose-300 shadow-lg shadow-rose-500/5 hover:border-rose-400"
                    : isMediumRisk && isPending
                    ? "bg-white border-amber-300 shadow-sm hover:border-amber-400"
                    : isPending
                    ? "bg-white border-slate-200/90 shadow-sm"
                    : "bg-slate-50/80 border-slate-200 opacity-75"
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-5">
                  {/* Left Column: Requester Information */}
                  <div className="flex-1 space-y-3">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <RiskBadge
                        category={item.riskCategory}
                        status={item.status}
                        score={item.riskScore}
                        size="md"
                      />
                      {item.verifiedMerchant && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-blue-500" /> NPCI Verified Merchant
                        </span>
                      )}
                      <span className="text-xs text-slate-400 font-mono">
                        Requested: {formatDateTime(item.requestedAt)}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-base font-bold text-slate-900 flex items-center gap-2">
                        {item.senderName}
                        {isHighRisk && (
                          <span className="text-[10px] uppercase font-bold text-rose-600 bg-rose-100 px-2 py-0.5 rounded-full">
                            Phishing Suspect
                          </span>
                        )}
                      </h4>
                      <p className="text-xs font-mono text-slate-500 mt-0.5">
                        Requester UPI VPA: <span className="font-semibold text-slate-700">{item.senderUpi}</span>
                      </p>
                    </div>

                    {/* Warning Message Box */}
                    <div
                      className={`p-3.5 rounded-xl border text-xs leading-relaxed ${
                        isHighRisk
                          ? "bg-rose-50/70 border-rose-200 text-rose-900"
                          : isMediumRisk
                          ? "bg-amber-50/70 border-amber-200 text-amber-900"
                          : "bg-blue-50/60 border-blue-200 text-blue-900"
                      }`}
                    >
                      <div className="font-bold flex items-center gap-1.5 mb-1">
                        {isHighRisk ? (
                          <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
                        ) : isMediumRisk ? (
                          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                        ) : (
                          <Info className="w-4 h-4 text-blue-600 shrink-0" />
                        )}
                        <span>{item.warningTitle}</span>
                      </div>
                      <p>{item.warningMessage}</p>
                    </div>

                    {/* Fraud Triggers Bullet List */}
                    {item.fraudTriggers && item.fraudTriggers.length > 0 && (
                      <div className="text-xs space-y-1">
                        <span className="font-bold text-slate-700 block">Threat Signals:</span>
                        <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                          {item.fraudTriggers.map((trig, idx) => (
                            <li key={idx} className="leading-snug">{trig}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Right Column: Amount & Action Buttons */}
                  <div className="lg:w-72 flex flex-col justify-between items-start lg:items-end gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                    <div className="w-full text-left lg:text-right">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                        Requested Debit Amount
                      </span>
                      <div className="text-2xl font-black text-slate-900 tracking-tight font-sans mt-0.5">
                        {formatCurrency(item.amount)}
                      </div>
                      <span className="text-[11px] text-rose-600 font-semibold block mt-0.5">
                        Will be debited from your bank account
                      </span>
                    </div>

                    {isPending ? (
                      <div className="w-full flex flex-col gap-2 pt-2 border-t border-slate-200">
                        {/* Reject button (Recommended for high risk) */}
                        <button
                          type="button"
                          onClick={() => handleOpenActionModal(item, "REJECT")}
                          className="w-full py-2.5 px-4 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-md shadow-rose-600/20 transition flex items-center justify-center gap-1.5"
                        >
                          <Ban className="w-4 h-4" />
                          <span>Reject & Block Payee</span>
                        </button>

                        {/* Accept button (With strong warning dialog) */}
                        <button
                          type="button"
                          onClick={() => handleOpenActionModal(item, "ACCEPT")}
                          className={`w-full py-2 px-4 rounded-xl border text-xs font-semibold transition flex items-center justify-center gap-1.5 ${
                            isHighRisk
                              ? "border-slate-300 text-slate-600 hover:bg-slate-200"
                              : "border-emerald-500 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                          }`}
                        >
                          <Check className="w-4 h-4 text-emerald-600" />
                          <span>Authorize Payment</span>
                        </button>
                      </div>
                    ) : (
                      <div className="w-full py-2 text-center text-xs font-bold text-slate-500 bg-slate-200/60 rounded-xl">
                        Status: {item.status.replace("_", " ")}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Confirmation Modal */}
      {activeModal && (
        <ConfirmationModal
          isOpen={true}
          onClose={() => setActiveModal(null)}
          onConfirm={handleConfirmAction}
          isLoading={actionLoading}
          type={activeModal.type === "ACCEPT" ? "danger" : "warning"}
          title={
            activeModal.type === "ACCEPT"
              ? confirmStep === 2
                ? "FINAL SECURITY OVERRIDE: Confirm Money Debit"
                : "Authorize Outbound Collect Debit?"
              : "Reject & Block Fraudulent Payee?"
          }
          confirmText={
            activeModal.type === "ACCEPT"
              ? confirmStep === 2
                ? "I Understand, Debit My Money"
                : "Proceed with Debit"
              : "Confirm Rejection"
          }
          cancelText="Cancel & Return"
          message={
            activeModal.type === "ACCEPT" ? (
              confirmStep === 2 ? (
                <div className="space-y-2 text-rose-900 bg-rose-50 p-3.5 rounded-xl border border-rose-300">
                  <p className="font-bold text-rose-700">
                    ⚠️ CRITICAL DANGER: This is almost certainly a scam!
                  </p>
                  <p>
                    You are about to transfer <strong>{formatCurrency(activeModal.request.amount)}</strong> to{" "}
                    <strong>{activeModal.request.senderUpi}</strong>.
                  </p>
                  <p>
                    You will NOT receive any reward, lottery, or refund. Funds transferred via UPI are irreversible once authenticated.
                  </p>
                </div>
              ) : (
                <div>
                  <p>
                    You are authorizing a transfer of{" "}
                    <strong>{formatCurrency(activeModal.request.amount)}</strong> to{" "}
                    <strong>{activeModal.request.senderName}</strong> ({activeModal.request.senderUpi}).
                  </p>
                  <p className="mt-2 text-slate-600">
                    Ensure that you initiated this purchase or consultation invoice. Remember that accepting a collect request sends money out of your account.
                  </p>
                </div>
              )
            ) : (
              <div>
                <p>
                  Are you sure you want to reject this collect request for{" "}
                  <strong>{formatCurrency(activeModal.request.amount)}</strong> from{" "}
                  <strong>{activeModal.request.senderName}</strong>?
                </p>
                <p className="mt-2 text-slate-600">
                  The request will be declined and the sender UPI ID ({activeModal.request.senderUpi}) will be logged in the dispute registry.
                </p>
              </div>
            )
          }
          extraDetails={
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-500">Requester VPA:</span>
                <span className="font-mono font-semibold text-slate-800">{activeModal.request.senderUpi}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Risk Assessment:</span>
                <span className="font-semibold text-rose-600">
                  {activeModal.request.riskCategory} RISK ({activeModal.request.riskScore}/100)
                </span>
              </div>
            </div>
          }
        />
      )}
    </div>
  );
};

export default CollectRequestWarning;
