import React from "react";
import { AlertOctagon, X, AlertTriangle, ShieldCheck } from "lucide-react";

export const ConfirmationModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  type = "danger", // "danger", "warning", "info", "success"
  isLoading = false,
  extraDetails = null
}) => {
  if (!isOpen) return null;

  const typeConfig = {
    danger: {
      icon: AlertOctagon,
      iconColor: "text-rose-500",
      iconBg: "bg-rose-500/10 border-rose-500/20",
      confirmBtn: "bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/30",
      borderGlow: "border-rose-500/30"
    },
    warning: {
      icon: AlertTriangle,
      iconColor: "text-amber-500",
      iconBg: "bg-amber-500/10 border-amber-500/20",
      confirmBtn: "bg-amber-600 hover:bg-amber-700 text-white shadow-amber-600/30",
      borderGlow: "border-amber-500/30"
    },
    success: {
      icon: ShieldCheck,
      iconColor: "text-emerald-500",
      iconBg: "bg-emerald-500/10 border-emerald-500/20",
      confirmBtn: "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/30",
      borderGlow: "border-emerald-500/30"
    }
  };

  const config = typeConfig[type] || typeConfig.danger;
  const Icon = config.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-sm animate-fade-in">
      <div
        className={`relative w-full max-w-lg overflow-hidden rounded-2xl bg-white border ${config.borderGlow} shadow-2xl transition-all`}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 pb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl border ${config.iconBg}`}>
              <Icon className={`w-6 h-6 ${config.iconColor}`} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">{title}</h3>
              <p className="text-xs text-slate-500">Action confirmation required</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-2">
          <div className="text-sm text-slate-600 leading-relaxed space-y-2">
            {typeof message === "string" ? <p>{message}</p> : message}
          </div>

          {extraDetails && (
            <div className="mt-4 p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1.5">
              {extraDetails}
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-end gap-3 p-6 pt-5 border-t border-slate-100 bg-slate-50/50">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2.5 rounded-xl text-sm font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-100 transition"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold shadow-md transition flex items-center gap-2 ${config.confirmBtn}`}
          >
            {isLoading && (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            )}
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;
