import React from "react";
import { SearchX, Inbox } from "lucide-react";

export const EmptyState = ({
  icon: Icon = Inbox,
  title = "No records found",
  description = "No matching transactions or activity found for the selected criteria.",
  actionText,
  onAction
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 my-4">
      <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-sm text-slate-400 mb-3">
        <Icon className="w-8 h-8 text-slate-400" />
      </div>
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      <p className="text-xs text-slate-500 mt-1 max-w-sm leading-relaxed">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-4 px-4 py-2 rounded-xl text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 transition border border-blue-200"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
