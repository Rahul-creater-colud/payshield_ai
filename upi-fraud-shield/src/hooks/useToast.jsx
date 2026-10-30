import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from "lucide-react";

const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    const newToast = {
      id,
      type: toast.type || "info",
      title: toast.title,
      message: toast.message,
      duration: toast.duration || 4500
    };

    setToasts((prev) => [...prev, newToast]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, newToast.duration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = {
    success: (message, title = "Success") => addToast({ type: "success", title, message }),
    error: (message, title = "Alert / Error") => addToast({ type: "error", title, message, duration: 6000 }),
    warning: (message, title = "Warning") => addToast({ type: "warning", title, message, duration: 5500 }),
    info: (message, title = "Information") => addToast({ type: "info", title, message })
  };

  return (
    <ToastContext.Provider value={{ toast, toasts, removeToast }}>
      {children}
      {/* Toast container floating at top-right */}
      <div className="fixed top-5 right-5 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none px-4">
        {toasts.map((item) => {
          const isSuccess = item.type === "success";
          const isError = item.type === "error";
          const isWarning = item.type === "warning";

          const bgClass = isSuccess
            ? "bg-emerald-950/90 border-emerald-500/40 text-emerald-100"
            : isError
            ? "bg-rose-950/90 border-rose-500/50 text-rose-100"
            : isWarning
            ? "bg-amber-950/90 border-amber-500/40 text-amber-100"
            : "bg-navy-900/90 border-blue-500/40 text-blue-100";

          const icon = isSuccess ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          ) : isError ? (
            <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          ) : isWarning ? (
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          ) : (
            <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
          );

          return (
            <div
              key={item.id}
              className={`pointer-events-auto p-4 rounded-xl border backdrop-blur-md shadow-2xl transition-all duration-300 transform translate-y-0 flex items-start gap-3 ${bgClass}`}
            >
              {icon}
              <div className="flex-1 min-w-0">
                {item.title && <h4 className="text-sm font-semibold tracking-wide">{item.title}</h4>}
                <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{item.message}</p>
              </div>
              <button
                onClick={() => removeToast(item.id)}
                className="text-slate-400 hover:text-white p-1 rounded transition shrink-0"
                aria-label="Dismiss"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context.toast;
};
