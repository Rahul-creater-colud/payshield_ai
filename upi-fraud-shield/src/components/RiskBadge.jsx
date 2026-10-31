import React from "react";
import { ShieldCheck, AlertTriangle, ShieldAlert, CheckCircle2, CircleHelp } from "lucide-react";

export const RiskBadge = ({ category = "LOW", status, score, size = "md", showScore = true }) => {
  const normCategory = (category || "LOW").toUpperCase();
  const normStatus = (status || "").toUpperCase();

  if (normCategory === "UNASSESSED" || normStatus === "UNASSESSED") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
        <CircleHelp className="h-3.5 w-3.5" />
        Not assessed
      </span>
    );
  }

  const isHigh = normCategory === "HIGH" || normCategory === "CRITICAL" || normStatus === "BLOCKED" || (score !== undefined && score >= 70);
  const isMedium = !isHigh && (normCategory === "MEDIUM" || normStatus === "SUSPICIOUS" || (score !== undefined && score >= 35));
  const isSafe = !isHigh && !isMedium;

  // Styling presets
  let bgClass = "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
  let dotClass = "bg-emerald-400";
  let label = "SAFE";
  let Icon = ShieldCheck;

  if (isHigh) {
    bgClass = "bg-rose-500/15 text-rose-400 border-rose-500/30 shadow-[0_0_12px_rgba(244,63,94,0.25)]";
    dotClass = "bg-rose-500 animate-ping";
    label = normStatus === "BLOCKED" ? "STOP / REVIEW" : "HIGH RISK";
    Icon = ShieldAlert;
  } else if (isMedium) {
    bgClass = "bg-amber-500/15 text-amber-400 border-amber-500/30 shadow-[0_0_10px_rgba(245,158,11,0.2)]";
    dotClass = "bg-amber-400";
    label = normStatus === "SUSPICIOUS" ? "SUSPICIOUS" : "MEDIUM RISK";
    Icon = AlertTriangle;
  } else {
    bgClass = "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    dotClass = "bg-emerald-400";
    label = normStatus === "SAFE" ? "SAFE" : "LOW RISK";
    Icon = CheckCircle2;
  }

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs font-medium gap-1",
    md: "px-2.5 py-1 text-xs font-semibold gap-1.5",
    lg: "px-3.5 py-1.5 text-sm font-bold gap-2"
  };

  return (
    <div className="inline-flex items-center gap-2">
      <span
        className={`inline-flex items-center rounded-full border backdrop-blur-sm transition-all ${bgClass} ${sizeClasses[size]}`}
      >
        <span className="relative flex h-2 w-2">
          {isHigh && <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${dotClass}`} />}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${isHigh ? "bg-rose-500" : isMedium ? "bg-amber-400" : "bg-emerald-400"}`} />
        </span>
        <Icon className={size === "lg" ? "w-4 h-4" : "w-3.5 h-3.5"} />
        <span>{label}</span>
      </span>

      {showScore && score !== undefined && (
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-mono font-semibold border ${
            isHigh
              ? "bg-rose-950/80 text-rose-300 border-rose-800/60"
              : isMedium
              ? "bg-amber-950/80 text-amber-300 border-amber-800/60"
              : "bg-emerald-950/80 text-emerald-300 border-emerald-800/60"
          }`}
        >
          {score}/100
        </span>
      )}
    </div>
  );
};

export default RiskBadge;
