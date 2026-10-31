import React from "react";
import { TrendingUp, TrendingDown, ArrowUpRight } from "lucide-react";

export const StatsCard = ({
  title,
  value,
  subvalue,
  change,
  isPositive,
  icon: Icon,
  variant = "default",
  onClick
}) => {
  const variantStyles = {
    default: "border-outline-soft bg-white text-slate-800 hover:border-blue-400",
    navy: "border-outline-soft bg-white text-slate-800 hover:border-blue-400",
    success: "border-emerald-200 bg-white text-slate-900 hover:border-emerald-400",
    warning: "border-amber-200 bg-white text-slate-900 hover:border-amber-400",
    danger: "border-rose-200 bg-white text-slate-900 hover:border-rose-400"
  };

  const iconBgStyles = {
    default: "bg-teal-50 text-brand-teal border-teal-100",
    navy: "bg-teal-50 text-brand-teal border-teal-100",
    success: "bg-emerald-50 text-emerald-700 border-emerald-100",
    warning: "bg-amber-50 text-amber-700 border-amber-100",
    danger: "bg-rose-50 text-rose-700 border-rose-100"
  };

  return (
    <div
      onClick={onClick}
      className={`relative overflow-hidden rounded-xl border p-4 transition-shadow duration-200 hover:shadow-fintech ${
        variantStyles[variant]
      } ${onClick ? "cursor-pointer" : ""}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-medium text-slate-500">
            {title}
          </p>
          <div className="mt-2 flex flex-wrap items-baseline gap-2">
            <h3 className="break-words text-xl font-semibold tracking-tight font-sans text-ink">
              {value}
            </h3>
            {subvalue && (
              <span className="text-[10px] font-normal text-slate-500">
                {subvalue}
              </span>
            )}
          </div>
        </div>

        {Icon && (
          <div className={`rounded-md border p-2 ${iconBgStyles[variant]}`}>
            <Icon className="h-4 w-4" />
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
          <span className="text-[11px] text-slate-500">
            vs prior 24h window
          </span>
        </div>
      )}
    </div>
  );
};

export default StatsCard;
