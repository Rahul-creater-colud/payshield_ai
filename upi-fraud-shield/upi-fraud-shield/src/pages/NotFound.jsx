import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShieldAlert, Home, ArrowLeft } from "lucide-react";

export const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4 animate-fade-in">
      <div className="w-20 h-20 rounded-3xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mb-6 shadow-sm">
        <ShieldAlert className="w-10 h-10" />
      </div>

      <span className="text-xs font-mono font-bold tracking-wider uppercase text-rose-500 bg-rose-50 px-3 py-1 rounded-full border border-rose-200">
        HTTP 404 — Routing Anomaly
      </span>

      <h1 className="text-3xl lg:text-4xl font-extrabold text-slate-900 mt-4 tracking-tight">
        Protected Page Not Found
      </h1>

      <p className="text-sm text-slate-500 mt-2 max-w-md leading-relaxed">
        The requested UPI defense endpoint or forensic dossier does not exist or may have been archived.
      </p>

      <div className="mt-6 flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs transition flex items-center gap-1.5 shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Go Back</span>
        </button>

        <Link
          to="/"
          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition flex items-center gap-1.5 shadow-md shadow-blue-600/20"
        >
          <Home className="w-4 h-4" />
          <span>Return to Command Center</span>
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
