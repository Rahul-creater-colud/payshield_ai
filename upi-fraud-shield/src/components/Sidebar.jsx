import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  AlertTriangle,
  BarChart3,
  Network,
  Store,
  Fingerprint,
  Link2,
  History,
  FileScan,
  FileText,
  ShieldCheck,
  Activity,
  X
} from "lucide-react";
import { useApiMode } from "../hooks/useApiMode";

export const Sidebar = ({ isOpen, onClose }) => {
  const { isBackendReachable, mode } = useApiMode();
  const navSections = [
    {
      label: "Workspace",
      items: [{ to: "/", label: "Dashboard", icon: LayoutDashboard }]
    },
    {
      label: "Detection",
      items: [
        { to: "/analyze", label: "Transaction Risk Checker", icon: ShieldCheck },
        { to: "/collect-requests", label: "Collect Request Protection", icon: AlertTriangle },
        { to: "/analytics", label: "Fraud Analytics", icon: BarChart3 },
        { to: "/fraud-network", label: "Fraud Network", icon: Network }
      ]
    },
    {
      label: "Investigation",
      items: [
        { to: "/merchant-verification", label: "Merchant Verification", icon: Store },
        { to: "/intelligence", label: "Intelligence & Grievances", icon: Fingerprint },
        { to: "/url-scanner", label: "Suspicious URL Scanner", icon: Link2 },
        { to: "/alerts-report", label: "Alerts & Risk Report", icon: FileText },
        { to: "/history", label: "Transaction History", icon: History },
        { to: "/screenshot-scanner", label: "Evidence Scanner", icon: FileScan }
      ]
    }
  ];

  return (
    <>
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-ink/50 backdrop-blur-sm lg:hidden"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-white/10 bg-sidebar text-white transition-transform duration-200 lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 px-5">
          <NavLink to="/" onClick={onClose} className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 text-teal-300">
              <ShieldCheck className="h-5 w-5" />
            </span>
            <div>
              <span className="block text-sm font-bold tracking-tight">PayShield AI</span>
              <span className="text-[10px] text-slate-300">Fraud operations</span>
            </div>
          </NavLink>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-300 hover:bg-white/10 hover:text-white lg:hidden"
            aria-label="Close sidebar navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
          {navSections.map((section) => (
            <section key={section.label}>
              <h2 className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400">
                {section.label}
              </h2>
              <div className="space-y-1">
                {section.items.map(({ to, label, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === "/"}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-md border-l-2 px-3 py-2.5 text-xs font-medium transition ${
                        isActive
                          ? "border-teal-400 bg-white/10 text-white"
                          : "border-transparent text-slate-300 hover:bg-white/5 hover:text-white"
                      }`
                    }
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="truncate">{label}</span>
                  </NavLink>
                ))}
              </div>
            </section>
          ))}
        </nav>

        <div className="shrink-0 border-t border-white/10 p-4">
          <div className="rounded-md border border-white/10 bg-white/5 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2 text-[11px] font-medium text-slate-200">
                <Activity className={`h-3.5 w-3.5 ${isBackendReachable ? "text-emerald-400" : "text-rose-400"}`} />
                Local Detection Service
              </span>
              <span className={`text-[9px] font-bold uppercase tracking-wide ${isBackendReachable ? "text-emerald-300" : "text-rose-300"}`}>
                {isBackendReachable ? "Connected" : "Offline"}
              </span>
            </div>
            <p className="mt-2 text-[10px] leading-4 text-slate-400">
              {mode === "MOCK" ? "Explicit demo fixtures selected." : "Heuristic prototype · synthetic records"}
            </p>
            <p className="text-[10px] leading-4 text-slate-400">No NPCI or payment-provider link</p>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
