import React from 'react';
import { Activity } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-200 bg-white px-6 py-3.5 text-slate-800 shadow-2xs">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-sm bg-blue-50 border border-blue-200 px-2 py-0.5 text-[10px] font-bold text-blue-700 uppercase tracking-wider">
              <Activity className="h-3 w-3" /> FDM & FEM Dual Solver
            </span>
            <span className="text-[11px] text-slate-500">
              Cancer Radiotherapy Poisson Transport Model
            </span>
          </div>
          <h1 className="text-lg font-bold text-slate-900 sm:text-xl mt-0.5 tracking-tight">
            Optimising Radiation Dose Distribution in Cancer Treatment
          </h1>
          <p className="text-xs text-slate-500">
            Finite Difference and Finite Element Methods for Reduced Healthy Tissue Exposure
          </p>
        </div>

        <div className="hidden sm:flex items-center gap-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-1.5 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-[11px] font-mono text-slate-700 font-medium">
              PPT Benchmark: D = 0.250000
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
