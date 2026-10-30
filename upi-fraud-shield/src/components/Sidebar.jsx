import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ShieldAlert,
  AlertTriangle,
  BarChart3,
  History,
  FileScan,
  FileText,
  ShieldCheck,
  ChevronRight,
  Zap,
  Activity,
  X
} from "lucide-react";
import { useApiMode } from "../hooks/useApiMode";

export const Sidebar = ({ isOpen, onClose }) => {
  const { isBackendReachable } = useApiMode();
  const navItems = [
    {
      to: "/",
      label: "Dashboard",
      icon: LayoutDashboard,
      badge: null,
      desc: "Stored records & metrics"
    },
    {
      to: "/analyze",
      label: "Transaction Analysis",
      icon: ShieldCheck,
      badge: "Local",
      desc: "Local rule-based test analysis"
    },
    {
      to: "/collect-requests",
      label: "Collect Requests",
      icon: AlertTriangle,
      badge: "Unavailable",
      badgeVariant: "info",
      desc: "No live request feed configured"
    },
    {
      to: "/analytics",
      label: "Fraud Analytics",
      icon: BarChart3,
      badge: null,
      desc: "Charts & Distributions"
    },
    {
      to: "/history",
      label: "Transaction History",
      icon: History,
      badge: null,
      desc: "Audit Logs & Search"
    },
    {
      to: "/screenshot-scanner",
      label: "Evidence Scanner",
      icon: FileScan,
      badge: "Demo",
      badgeVariant: "info",
      desc: "Sample results; OCR unavailable"
    },
    {
      to: "/alerts-report",
      label: "Alerts & Risk Report",
      icon: ShieldAlert,
      badge: null,
      desc: "Stored heuristic assessments"
    }
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-navy-950/70 backdrop-blur-sm lg:hidden transition-opacity"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-gradient-to-b from-navy-950 via-navy-900 to-navy-950 border-r border-navy-800 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand Header */}
        <div className="p-5 border-b border-navy-800/80 flex items-center justify-between">
          <NavLink to="/" onClick={onClose} className="flex items-center gap-3 group">
            <div className="relative flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-0.5 shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
              <div className="w-full h-full bg-navy-950 rounded-[10px] flex items-center justify-center">
                <ShieldCheck className="w-6 h-6 text-cyan-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-base tracking-tight text-white font-sans">
                  UPI<span className="text-cyan-400">SHIELD</span>
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-blue-500/20 text-cyan-300 border border-blue-400/30">
                  AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Problem 3.2 Hackathon</p>
            </div>
          </NavLink>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-navy-800 lg:hidden transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Section */}
        <div className="flex-1 overflow-y-auto px-3.5 py-4 space-y-1.5">
          <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Local Heuristic Tools
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `group relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-blue-600/30 via-blue-500/20 to-transparent text-white border-l-4 border-cyan-400 shadow-sm"
                      : "text-slate-400 hover:text-slate-100 hover:bg-navy-800/60"
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0 transition-colors text-slate-400 group-hover:text-cyan-400" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="truncate font-semibold text-slate-200">{item.label}</span>
                    {item.badge && (
                      <span
                        className={`ml-2 px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          item.badgeVariant === "high"
                            ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                            : item.badgeVariant === "info"
                            ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                            : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-400 truncate mt-0.5">{item.desc}</p>
                </div>
              </NavLink>
            );
          })}
        </div>

        {/* Engine status & Footer Info */}
        <div className="p-4 border-t border-navy-800/80 bg-navy-950/60">
          <div className="p-3 rounded-xl bg-navy-900/90 border border-navy-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                <Activity className={`w-3.5 h-3.5 ${isBackendReachable ? "text-emerald-400" : "text-rose-400"}`} /> Local Detection Service
              </span>
              <span className={`${isBackendReachable ? "text-emerald-400" : "text-rose-400"} font-semibold text-[11px]`}>
                {isBackendReachable ? "CONNECTED" : "OFFLINE"}
              </span>
            </div>
            <div className="h-1.5 w-full bg-navy-950 rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${isBackendReachable ? "bg-emerald-500 w-full" : "bg-rose-500 w-0"}`} />
            </div>
            <div className="flex items-center justify-between text-[10px] text-slate-400">
              <span>Local heuristic rules</span>
              <span>No NPCI connection</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
