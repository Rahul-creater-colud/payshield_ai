import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Menu,
  ShieldCheck,
  Search,
  Bell,
  PhoneCall,
  Sparkles,
  ExternalLink,
  HelpCircle
} from "lucide-react";
import { useApiMode } from "../hooks/useApiMode";

const pageTitles = {
  "/": { title: "Command Center Dashboard", subtitle: "Real-time UPI transaction monitoring & fraud velocity" },
  "/analyze": { title: "Transaction Risk Analysis", subtitle: "Instant neural risk scoring and heuristic breakdown" },
  "/collect-requests": { title: "Collect Request Shield", subtitle: "Reverse-debit & scam collect request interception" },
  "/analytics": { title: "Fraud Analytics & Distributions", subtitle: "Aggregate fraud volumes, vectors, and risk trends" },
  "/history": { title: "Transaction Audit History", subtitle: "Searchable transaction records with forensic risk markers" },
  "/screenshot-scanner": { title: "Evidence & Screenshot Scanner", subtitle: "AI Vision & OCR inspection of scam payment receipts" },
  "/alerts-report": { title: "Security Alerts & Risk Report", subtitle: "Critical threat intelligence and prevention protocols" }
};

export const Navbar = ({ onToggleSidebar }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isLiveMode, mode } = useApiMode();

  const currentMeta = pageTitles[location.pathname] || {
    title: "UPI Fraud Detection System",
    subtitle: "Problem Statement 3.2 — Digital Payment Security"
  };

  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
      <div className="px-4 lg:px-8 py-3.5 flex items-center justify-between gap-4">
        {/* Left: Mobile hamburger & Page Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 lg:hidden transition"
            aria-label="Open sidebar navigation"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg lg:text-xl font-bold text-slate-900 tracking-tight">
                {currentMeta.title}
              </h1>
              <span
                className={`hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  isLiveMode
                    ? "bg-purple-100 text-purple-700 border border-purple-200"
                    : "bg-blue-100 text-blue-700 border border-blue-200"
                }`}
              >
                {mode} DATA
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">{currentMeta.subtitle}</p>
          </div>
        </div>

        {/* Right: Quick actions & Hackathon badge */}
        <div className="flex items-center gap-2.5">
          {/* National Cybercrime Helpline 1930 */}
          <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold">
            <PhoneCall className="w-3.5 h-3.5 text-rose-600 animate-bounce" />
            <span>Cybercrime Helpline: 1930</span>
          </div>

          {/* Quick analyze action button */}
          {location.pathname !== "/analyze" && (
            <button
              onClick={() => navigate("/analyze")}
              className="hidden md:flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-cyan-300" />
              <span>Score New UPI</span>
            </button>
          )}

          {/* Notification bell to Alerts */}
          <button
            onClick={() => navigate("/alerts-report")}
            className="relative p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition"
            title="View Security Alerts"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
            </span>
          </button>

          {/* User Badge */}
          <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-navy-900 to-blue-700 text-white flex items-center justify-center font-bold text-xs shadow-sm">
              M3
            </div>
            <div className="hidden md:block text-left">
              <p className="text-xs font-bold text-slate-800 leading-tight">Member 3</p>
              <p className="text-[10px] text-slate-500 leading-tight">Frontend / UI Lead</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
