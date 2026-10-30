import React from "react";
import { TrendingUp, TrendingDown, ArrowUpRight } from "lucide-react";

export const StatsCard = ({
  title,
  value,
  subvalue,
  change,
  isPositive,
  icon: Icon,
  variant = "default", // "default", "success", "warning", "danger", "navy"
  onClick
}) => {
  const variantStyles = {
    default: "border-slate-200/80 bg-white text-slate-800 hover:border-blue-400",
    navy: "border-navy-800 bg-gradient-to-br from-navy-900 to-navy-950 text-white hover:border-blue-500/50 shadow-xl",
    success: "border-emerald-500/30 bg-emerald-50/40 text-slate-900 hover:border-emerald-500",
    warning: "border-amber-500/30 bg-amber-50/40 text-slate-900 hover:border-amber-500",
    danger: "border-rose-500/30 bg-rose-50/40 text-slate-900 hover:border-rose-500"
  };

  const iconBgStyles = {
    default: "bg-blue-50 text-blue-600 border-blue-100",
    navy: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    success: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-600 border-amber-500/20",
    danger: "bg-rose-500/10 text-rose-600 border-rose-500/20"
  };

  const isDark = variant === "navy";

  return (
    <div
      onClick={onClick}
      className={`relative overflow-hidden rounded-2xl border p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg ${
        variantStyles[variant]
      } ${onClick ? "cursor-pointer" : ""}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className={`text-xs font-medium uppercase tracking-wider ${isDark ? "text-slate-400" : "text-slate-500"}`}>
            {title}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <h3 className={`text-2xl font-bold tracking-tight font-sans ${isDark ? "text-white" : "text-slate-900"}`}>
              {value}
            </h3>
            {subvalue && (
              <span className={`text-xs font-normal ${isDark ? "text-slate-400" : "text-slate-500"}`}>
                {subvalue}
              </span>
            )}
          </div>
        </div>

        {Icon && (
          <div className={`p-3 rounded-xl border ${iconBgStyles[variant]}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {change !== undefined && (
        <div className="mt-3 flex items-center gap-1.5 text-xs">
          <span
            className={`inline-flex items-center gap-0.5 font-medium px-1.5 py-0.5 rounded ${
              isPositive
                ? "bg-emerald-500/10 text-emerald-600 font-semibold"
                : "bg-rose-500/10 text-rose-600 font-semibold"
            }`}
          >
            {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {change}
          </span>
          <span className={`text-[11px] ${isDark ? "text-slate-400" : "text-slate-500"}`}>
            vs prior 24h window
          </span>
        </div>
      )}
    </div>
  );
};

export default StatsCard;
