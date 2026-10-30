import React from "react";
import { ShieldCheck, Radar } from "lucide-react";

export const LoadingSpinner = ({
  message = "Analyzing transaction with AI threat intelligence...",
  subtext = "Local heuristic processing; no payment is executed or blocked",
  size = "md"
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center animate-fade-in">
      <div className="relative flex items-center justify-center mb-5">
        {/* Outer pulsing ring */}
        <div className="absolute w-20 h-20 rounded-full border-2 border-blue-500/20 animate-ping opacity-60" />
        <div className="absolute w-16 h-16 rounded-full border-2 border-blue-400/40 animate-pulse" />
        
        {/* Core spinner ring */}
        <div className="w-14 h-14 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin" />
        
        {/* Center Shield icon */}
        <div className="absolute flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white shadow-md">
          <ShieldCheck className="w-4 h-4 animate-pulse" />
        </div>
      </div>

      <h4 className="text-base font-semibold text-slate-800 tracking-tight">{message}</h4>
      {subtext && <p className="text-xs text-slate-500 mt-1 max-w-md">{subtext}</p>}
    </div>
  );
};

export default LoadingSpinner;
