import React from 'react';
import { ModelParams } from '../types';
import {
  LayoutDashboard,
  Layers,
  Cpu,
  Triangle,
  GitCompare,
  TrendingDown,
  Sliders,
  Sparkles,
  CheckCircle2,
  FileText,
  Code2,
  RotateCcw,
  Play
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  params: ModelParams;
  setParams: React.Dispatch<React.SetStateAction<ModelParams>>;
  onResetDefault: () => void;
  onRunSimulation: () => void;
  isValid: boolean;
  validationError?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  params,
  setParams,
  onResetDefault,
  onRunSimulation,
  isValid,
  validationError
}) => {
  const navItems = [
    { id: 'overview', label: 'Project Overview', icon: LayoutDashboard },
    { id: 'module1', label: 'Module 1: Mathematical Model', icon: Layers },
    { id: 'module2', label: 'Module 2: FDM Numerical Solution', icon: Cpu },
    { id: 'module3', label: 'Module 3: FEM & Validation', icon: Triangle },
    { id: 'comparison', label: 'FDM vs FEM Comparison', icon: GitCompare },
    { id: 'convergence', label: 'Multi-Grid Convergence', icon: TrendingDown },
    { id: 'sensitivity', label: 'Sensitivity & Tissue Exposure', icon: Sliders },
    { id: 'visualizations', label: 'Advanced Visualizations', icon: Sparkles },
    { id: 'verification', label: 'Automated Verification Tests', icon: CheckCircle2 },
    { id: 'report', label: 'Results & Research Report', icon: FileText },
    { id: 'code', label: 'Python Source & Files', icon: Code2 }
  ];

  return (
    <aside className="w-72 shrink-0 border-r border-slate-200 bg-slate-50 flex flex-col justify-between overflow-y-auto p-4 select-none text-slate-700">
      <div className="space-y-4">
        {/* Status Box */}
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
          <p className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold">Dual Solver Status</p>
          <div className="mt-1 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-xs font-semibold text-slate-800">FDM + FEM Ready</span>
            </div>
            <span className="text-[10px] font-mono text-blue-700 bg-blue-50 border border-blue-100 px-1.5 py-0.5 rounded font-medium">
              Dual Solver
            </span>
          </div>
        </div>

        {/* Navigation Section */}
        <div>
          <div className="mb-1.5 px-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Research Modules
          </div>
          <nav className="space-y-0.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  id={`nav-btn-${item.id}`}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium transition-all text-left ${
                    isActive
                      ? 'bg-blue-600 text-white font-semibold shadow-xs'
                      : 'text-slate-600 hover:bg-slate-200/60 hover:text-slate-900'
                  }`}
                >
                  <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Simulation Parameter Controls */}
        <div className="space-y-2.5 pt-3 border-t border-slate-200">
          <div className="flex items-center justify-between px-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Model Parameters
            </span>
            <button
              onClick={onResetDefault}
              className="flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800 transition-colors"
              title="Reset to PPT benchmark case (Lx=1, Ly=1, k=1, S=4, h=0.5, Db=0)"
            >
              <RotateCcw className="h-3 w-3" /> Reset
            </button>
          </div>

          <div className="space-y-2.5 rounded-xl border border-slate-200 bg-white p-3 shadow-xs text-xs">
            {/* Diffusion Coefficient k */}
            <div>
              <div className="flex justify-between text-slate-600 font-medium">
                <span className="text-[11px]">Diffusion Coeff (k)</span>
                <span className="font-mono text-blue-700 font-bold">{params.k}</span>
              </div>
              <input
                type="number"
                step="0.1"
                min="0.05"
                max="10.0"
                value={params.k}
                onChange={(e) =>
                  setParams((p) => ({ ...p, k: parseFloat(e.target.value) || 1.0 }))
                }
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Source Intensity S */}
            <div>
              <div className="flex justify-between text-slate-600 font-medium">
                <span className="text-[11px]">Source Intensity (S)</span>
                <span className="font-mono text-amber-600 font-bold">{params.S}</span>
              </div>
              <input
                type="number"
                step="0.5"
                min="0.1"
                max="50.0"
                value={params.S}
                onChange={(e) =>
                  setParams((p) => ({ ...p, S: parseFloat(e.target.value) || 4.0 }))
                }
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Grid Spacing h */}
            <div>
              <div className="flex justify-between text-slate-600 font-medium">
                <span className="text-[11px]">Grid Spacing (h)</span>
                <span className="font-mono font-bold text-teal-700">{params.h}</span>
              </div>
              <select
                value={params.h}
                onChange={(e) =>
                  setParams((p) => ({ ...p, h: parseFloat(e.target.value) }))
                }
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-xs text-slate-800 focus:border-blue-500 focus:outline-none cursor-pointer"
              >
                <option value="0.5">h = 0.5 (PPT Benchmark Case)</option>
                <option value="0.25">h = 0.25 (Refined 5×5 Mesh)</option>
                <option value="0.2">h = 0.20 (Standard 6×6 Mesh)</option>
                <option value="0.125">h = 0.125 (Fine 9×9 Mesh)</option>
                <option value="0.1">h = 0.10 (High Res 11×11 Mesh)</option>
              </select>
            </div>

            {/* Boundary Condition */}
            <div>
              <div className="flex justify-between text-slate-600 font-medium">
                <span className="text-[11px]">Boundary Dose (Db)</span>
                <span className="font-mono text-slate-800">{params.boundaryDose}</span>
              </div>
              <input
                type="number"
                step="0.1"
                value={params.boundaryDose}
                onChange={(e) =>
                  setParams((p) => ({
                    ...p,
                    boundaryDose: parseFloat(e.target.value) || 0.0
                  }))
                }
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          {!isValid && validationError && (
            <div className="rounded-lg border border-rose-300 bg-rose-50 p-2 text-[11px] text-rose-700">
              {validationError}
            </div>
          )}

          <button
            id="run-fdm-btn"
            onClick={onRunSimulation}
            disabled={!isValid}
            className={`flex w-full items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-bold text-white transition-all shadow-xs cursor-pointer ${
              isValid
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-slate-300 cursor-not-allowed text-slate-500'
            }`}
          >
            <Play className="h-3.5 w-3.5 fill-white" /> RUN DUAL SOLVER (FDM & FEM)
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="pt-3 text-center text-[10px] text-slate-400 border-t border-slate-200">
        <div className="font-semibold uppercase tracking-wider text-slate-500">Dual FDM & FEM Solver</div>
        <div className="font-mono text-[9px] mt-0.5">Cancer Radiotherapy Optimization</div>
      </div>
    </aside>
  );
};
