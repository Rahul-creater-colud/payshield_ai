import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Menu,
  RefreshCw,
  Sparkles,
  ToggleLeft,
  ToggleRight
} from "lucide-react";
import { useApiMode } from "../hooks/useApiMode";
import { useToast } from "../hooks/useToast";

const pageTitles = {
  "/": { title: "Dashboard", subtitle: "Stored transaction records and local risk assessments" },
  "/analyze": { title: "Transaction Risk Checker", subtitle: "Local heuristic assessment · no payment is executed" },
  "/collect-requests": { title: "Collect Request Protection", subtitle: "Live request monitoring and payment controls are unavailable" },
  "/analytics": { title: "Fraud Analytics & Model Status", subtitle: "Stored synthetic telemetry · local heuristic engine · no validated ML benchmark" },
  "/fraud-network": { title: "Fraud Network", subtitle: "Stored account relationships and heuristic graph patterns" },
  "/merchant-verification": { title: "Merchant Verification", subtitle: "Local account lookup only · no external merchant verification" },
  "/intelligence": { title: "Fraud Intelligence & Grievance Centre", subtitle: "Local indicator registry and prototype review workflow" },
  "/url-scanner": { title: "Suspicious URL Scanner", subtitle: "Static local heuristics · URLs are not opened or fetched" },
  "/history": { title: "Transaction History", subtitle: "Stored inputs and assessments · not a payment-provider ledger" },
  "/screenshot-scanner": { title: "Evidence Scanner", subtitle: "Sample responses only · uploaded-image OCR is unavailable" },
  "/alerts-report": { title: "Risk Assessments & Review Notes", subtitle: "Internal heuristic records · no external incident response" }
};

export const Navbar = ({ onToggleSidebar }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const toast = useToast();
  const { mode, isBackendReachable, isCheckingBackend, checkConnectivity, toggleMode } = useApiMode();

  const currentMeta = pageTitles[location.pathname] || {
    title: "PayShield AI",
    subtitle: "Local fraud-risk assessment prototype"
  };

  return (
    <header className="sticky top-0 z-30 border-b border-outline-soft bg-white/95 backdrop-blur">
      <div className="flex min-h-16 items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="rounded-md p-2 text-slate-600 hover:bg-surface-container lg:hidden"
            aria-label="Open sidebar navigation"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold tracking-tight text-ink sm:text-lg">{currentMeta.title}</h1>
            <p className="hidden truncate text-xs text-slate-500 sm:block">{currentMeta.subtitle}</p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <div className="hidden items-center gap-2 rounded-md border border-outline-soft bg-canvas px-3 py-1.5 text-[10px] font-semibold text-slate-700 md:flex">
            <span className={`h-2 w-2 rounded-full ${isBackendReachable ? "bg-emerald-500" : "bg-rose-500"}`} />
            {isBackendReachable ? "LOCAL SERVICE CONNECTED" : "BACKEND DISCONNECTED"}
          </div>
          {location.pathname !== "/analyze" && (
            <button
              onClick={() => navigate("/analyze")}
              className="hidden items-center gap-1.5 rounded-md bg-brand-teal px-3 py-2 text-xs font-semibold text-white transition hover:bg-blue-700 md:flex"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Check transaction</span>
            </button>
          )}
          <button
            type="button"
            onClick={async () => {
              const connected = await checkConnectivity();
              toast[connected ? "success" : "warning"](
                connected
                  ? "Local FastAPI service is reachable. Records may include synthetic seeds; no payment-provider data is connected."
                  : "The backend is unavailable. Live API data cannot be loaded.",
                connected ? "Local service connected" : "Backend disconnected"
              );
            }}
            disabled={isCheckingBackend}
            className="rounded-md border border-outline-soft bg-white p-2 text-slate-600 hover:bg-surface-container disabled:opacity-60"
            title="Check local backend connection"
            aria-label="Check local backend connection"
          >
            <RefreshCw className={`h-4 w-4 ${isCheckingBackend ? "animate-spin" : ""}`} />
          </button>
          <span className="hidden rounded-md border border-amber-200 bg-amber-50 px-2 py-1.5 text-[9px] font-bold tracking-wide text-amber-800 lg:inline-flex">
            {mode === "MOCK" ? "DEMO DATA" : "LOCAL PROTOTYPE DATA"}
          </span>
          <button
            type="button"
            onClick={() => toggleMode(mode === "MOCK" ? "LIVE" : "MOCK")}
            className="inline-flex items-center gap-1 rounded-md border border-outline-soft bg-white px-2.5 py-2 text-[10px] font-semibold text-slate-700 hover:bg-surface-container"
            aria-label={mode === "MOCK" ? "Switch to local API mode" : "Switch to demo mode"}
          >
            {mode === "MOCK" ? <ToggleLeft className="h-4 w-4 text-amber-600" /> : <ToggleRight className="h-4 w-4 text-brand-teal" />}
            <span>{mode === "MOCK" ? "DEMO" : "LOCAL API"}</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
