import React from "react";
import { Server, ToggleLeft, ToggleRight, RefreshCw, AlertCircle, CheckCircle2, ShieldAlert } from "lucide-react";
import { useApiMode } from "../hooks/useApiMode";
import { useToast } from "../hooks/useToast";
import { API_BASE_URL } from "../api/axiosClient";

export const ApiStatusBanner = () => {
  const {
    mode,
    isLiveMode,
    isMockMode,
    toggleMode,
    isBackendReachable,
    isCheckingBackend,
    checkConnectivity
  } = useApiMode();
  const toast = useToast();

  const handleToggle = () => {
    const nextMode = isMockMode ? "LIVE" : "MOCK";
    toggleMode(nextMode);
    toast.info(
      nextMode === "LIVE"
        ? "Switched to Local API mode. Connecting to the PayShield backend."
        : "Switched to explicit DEMO mode. Displayed records and actions are synthetic.",
      `API Mode: ${nextMode}`
    );
  };

  const handleTestPing = async () => {
    const ok = await checkConnectivity();
    if (ok) {
      toast.success("Backend FastAPI connected successfully (200 OK)", "FastAPI Online");
    } else {
      toast.warning(
        "Could not connect to the PayShield backend. Live data is unavailable; no mock data will be substituted.",
        "Backend Unreachable"
      );
    }
  };

  return (
    <div
      className={`border-b text-xs transition-colors duration-300 ${
        isLiveMode
          ? isBackendReachable
            ? "bg-emerald-950/40 border-emerald-800/40 text-emerald-300"
            : "bg-rose-950/40 border-rose-800/40 text-rose-300"
          : "bg-navy-900/60 border-navy-800 text-slate-300"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 py-2 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2 w-2">
            <span
              className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isLiveMode
                  ? isBackendReachable
                    ? "bg-emerald-400 animate-ping"
                    : "bg-rose-400 animate-ping"
                  : "bg-blue-400"
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isLiveMode
                  ? isBackendReachable
                    ? "bg-emerald-500"
                    : "bg-rose-500"
                  : "bg-blue-400"
              }`}
            />
          </span>

          <span className="font-semibold tracking-wide">
            {isLiveMode ? (
              isBackendReachable ? (
                <span className="text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 inline" /> LOCAL BACKEND CONNECTED (FastAPI @ {API_BASE_URL})
                </span>
              ) : (
                <span className="text-rose-400 flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 inline" /> BACKEND DISCONNECTED — Live data unavailable
                </span>
              )
            ) : (
              <span className="text-blue-300 flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 inline text-blue-400" /> MOCK SIMULATION MODE ACTIVE (Full standalone demo ready)
              </span>
            )}
          </span>

          <span className="hidden md:inline text-slate-400 text-[11px] border-l border-slate-700/60 pl-2.5">
            {isLiveMode
              ? isBackendReachable
                ? "Local rule-based service connected • DEMO / SYNTHETIC DATA"
                : "No data displayed until the backend reconnects."
              : "Explicit demo data and simulated actions • not live UPI monitoring."}
          </span>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <button
            onClick={handleTestPing}
            disabled={isCheckingBackend}
            className="px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition flex items-center gap-1 text-[11px]"
            title="Ping backend health endpoint"
          >
            <RefreshCw className={`w-3 h-3 ${isCheckingBackend ? "animate-spin text-blue-400" : ""}`} />
            <span>{isCheckingBackend ? "Checking..." : "Ping Backend"}</span>
          </button>

          <button
            onClick={handleToggle}
            className={`px-3 py-1 rounded-md font-medium transition flex items-center gap-1.5 text-[11px] border ${
              isLiveMode
                ? "bg-blue-600/20 text-blue-300 border-blue-500/40 hover:bg-blue-600/30"
                : "bg-emerald-600/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-600/30"
            }`}
          >
            {isLiveMode ? <ToggleRight className="w-4 h-4 text-blue-400" /> : <ToggleLeft className="w-4 h-4 text-emerald-400" />}
            <span>Mode: {mode}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApiStatusBanner;
