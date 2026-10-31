import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

export const PageHeading = ({ eyebrow, title, description, actions }) => (
  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
    <div>
      {eyebrow && (
        <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.12em] text-brand-teal">
          {eyebrow}
        </p>
      )}
      <h2 className="text-xl font-semibold tracking-tight text-ink sm:text-2xl">{title}</h2>
      {description && <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">{description}</p>}
    </div>
    {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
  </div>
);

export const MetricCard = ({ label, value, detail, icon: Icon, tone = "teal" }) => {
  const tones = {
    teal: "bg-teal-50 text-brand-teal",
    red: "bg-rose-50 text-rose-700",
    amber: "bg-amber-50 text-amber-700",
    green: "bg-emerald-50 text-emerald-700",
    slate: "bg-slate-100 text-slate-600"
  };

  return (
    <section className="surface-card min-w-0 p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium text-slate-500">{label}</p>
          <p className="mt-2 break-words text-2xl font-semibold tracking-tight text-ink">{value}</p>
        </div>
        {Icon && (
          <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md ${tones[tone]}`}>
            <Icon className="h-4 w-4" />
          </span>
        )}
      </div>
      {detail && <p className="mt-2 text-[11px] leading-4 text-slate-500">{detail}</p>}
    </section>
  );
};

export const DataNotice = ({ children, tone = "info" }) => {
  const styles = {
    info: "border-sky-200 bg-sky-50 text-sky-900",
    warning: "border-amber-200 bg-amber-50 text-amber-900",
    danger: "border-rose-200 bg-rose-50 text-rose-900"
  };
  return (
    <div className={`flex items-start gap-2 rounded-md border px-3 py-2.5 text-xs leading-5 ${styles[tone]}`}>
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
};

export const ErrorPanel = ({ title = "Data unavailable", error, onRetry }) => (
  <section className="surface-card p-6 text-center sm:p-8">
    <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-rose-50 text-rose-700">
      <AlertCircle className="h-5 w-5" />
    </div>
    <h3 className="mt-3 text-base font-semibold text-ink">{title}</h3>
    <p className="mx-auto mt-1 max-w-xl text-sm text-slate-600">{error}</p>
    {onRetry && (
      <button type="button" onClick={onRetry} className="btn-primary mt-4">
        <RefreshCw className="h-4 w-4" />
        Retry
      </button>
    )}
  </section>
);

export const DataLabel = ({ children = "LOCAL PROTOTYPE RECORDS" }) => (
  <span className="inline-flex items-center rounded border border-amber-200 bg-amber-50 px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-amber-800">
    {children}
  </span>
);
