import React from 'react';
import { Zap } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-800 bg-[#0f172a] px-6 py-4 text-slate-200">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded bg-indigo-600/20 border border-indigo-500/30 px-2 py-0.5 text-[10px] font-bold text-indigo-400 uppercase tracking-wider">
              <Zap className="h-3 w-3" /> RAD-OPTIMIZE v1.0 • Capstone
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Finite Difference Method • Diffusion Equation Simulation
            </span>
          </div>
          <h1 className="text-xl font-bold text-white sm:text-2xl mt-1 tracking-tight">
            Radiation Dose Distribution Optimizer
          </h1>
          <p className="text-xs text-slate-400">
            Analytical Verification & Healthy Tissue Sparing for Elliptic Dose Transport
          </p>
        </div>

        <div className="hidden sm:flex items-center gap-3">
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 px-3.5 py-1.5 flex items-center gap-2.5">
            <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></div>
            <span className="text-[11px] font-mono text-slate-300 uppercase tracking-tight">
              Benchmark: 0.250000 Gy
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

