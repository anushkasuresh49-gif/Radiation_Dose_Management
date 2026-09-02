import React from 'react';
import { ModelParams } from '../types';
import {
  LayoutDashboard,
  Layers,
  Cpu,
  CheckCircle2,
  TrendingDown,
  Sliders,
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
    { id: 'module1', label: 'Module 1: Modelling', icon: Layers },
    { id: 'module2', label: 'Module 2: FDM Solver', icon: Cpu },
    { id: 'module3', label: 'Module 3: Validation', icon: CheckCircle2 },
    { id: 'convergence', label: 'Convergence Analysis', icon: TrendingDown },
    { id: 'sensitivity', label: 'Parameter Sensitivity', icon: Sliders },
    { id: 'report', label: 'Results & Report', icon: FileText },
    { id: 'code', label: 'Python Code & Files', icon: Code2 }
  ];

  return (
    <aside className="w-72 shrink-0 border-r border-slate-800 bg-[#0f172a] flex flex-col justify-between overflow-y-auto p-4 select-none text-slate-200">
      <div className="space-y-5">
        {/* Computational Status Box */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-3.5 shadow-sm">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Computational Status</p>
          <div className="mt-1.5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-400"></div>
              <span className="text-xs font-mono text-slate-200 uppercase font-bold tracking-tight">System Ready</span>
            </div>
            <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/60 border border-indigo-800/50 px-1.5 py-0.5 rounded">
              Direct Solver
            </span>
          </div>
        </div>

        {/* Navigation Section */}
        <div>
          <div className="mb-2 px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
            Research Modules
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  id={`nav-btn-${item.id}`}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600/25 text-indigo-300 border border-indigo-500/30 font-semibold shadow-xs'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Simulation Parameter Controls */}
        <div className="space-y-3 pt-3 border-t border-slate-800">
          <div className="flex items-center justify-between px-1">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
              Input Parameters
            </span>
            <button
              onClick={onResetDefault}
              className="flex items-center gap-1 text-[11px] font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
              title="Reset parameters to canonical test case (Lx=1, Ly=1, k=1, S=4, h=0.5, D=0)"
            >
              <RotateCcw className="h-3 w-3" /> Reset
            </button>
          </div>

          <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 shadow-xs text-xs">
            {/* Domain Length Lx */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium">
                <span className="text-slate-400 text-[11px]">Domain X (Lx)</span>
                <span className="font-mono text-slate-200">{params.xmax - params.xmin}</span>
              </div>
              <input
                type="number"
                step="0.1"
                min="0.2"
                max="5.0"
                value={params.xmax}
                onChange={(e) =>
                  setParams((p) => ({ ...p, xmax: parseFloat(e.target.value) || 1.0 }))
                }
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2.5 py-1 font-mono text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            {/* Domain Length Ly */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium">
                <span className="text-slate-400 text-[11px]">Domain Y (Ly)</span>
                <span className="font-mono text-slate-200">{params.ymax - params.ymin}</span>
              </div>
              <input
                type="number"
                step="0.1"
                min="0.2"
                max="5.0"
                value={params.ymax}
                onChange={(e) =>
                  setParams((p) => ({ ...p, ymax: parseFloat(e.target.value) || 1.0 }))
                }
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2.5 py-1 font-mono text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            {/* Diffusion Coefficient k */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium">
                <span className="text-slate-400 text-[11px]">Diffusion (k)</span>
                <span className="font-mono text-indigo-400 font-semibold">{params.k}</span>
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
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2.5 py-1 font-mono text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            {/* Source Intensity S */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium">
                <span className="text-slate-400 text-[11px]">Source (S)</span>
                <span className="font-mono text-amber-400 font-semibold">{params.S}</span>
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
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2.5 py-1 font-mono text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            {/* Grid Spacing h */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium">
                <span className="text-slate-400 text-[11px]">Grid Spacing (h)</span>
                <span className="font-mono font-semibold text-indigo-400">{params.h}</span>
              </div>
              <select
                value={params.h}
                onChange={(e) =>
                  setParams((p) => ({ ...p, h: parseFloat(e.target.value) }))
                }
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2.5 py-1 font-mono text-xs text-slate-100 focus:border-indigo-500 focus:outline-none cursor-pointer"
              >
                <option value="0.5">h = 0.5 (Canonical 3×3 Grid)</option>
                <option value="0.25">h = 0.25 (Refined 5×5 Grid)</option>
                <option value="0.2">h = 0.20 (Standard 6×6 Grid)</option>
                <option value="0.1">h = 0.10 (High Res 11×11 Grid)</option>
                <option value="0.05">h = 0.05 (Fine 21×21 Grid)</option>
              </select>
            </div>

            {/* Boundary Condition */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium">
                <span className="text-slate-400 text-[11px]">Boundary (D_b)</span>
                <span className="font-mono text-slate-200">{params.boundaryDose}</span>
              </div>
              <input
                type="number"
                step="0.05"
                value={params.boundaryDose}
                onChange={(e) =>
                  setParams((p) => ({
                    ...p,
                    boundaryDose: parseFloat(e.target.value) || 0.0
                  }))
                }
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2.5 py-1 font-mono text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          {!isValid && validationError && (
            <div className="rounded-lg border border-rose-500/30 bg-rose-950/40 p-2 text-[11px] text-rose-300">
              {validationError}
            </div>
          )}

          <button
            id="run-fdm-btn"
            onClick={onRunSimulation}
            disabled={!isValid}
            className={`flex w-full items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-bold text-white transition-all shadow-md ${
              isValid
                ? 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-600/30 cursor-pointer'
                : 'bg-slate-800 cursor-not-allowed text-slate-500 border border-slate-700'
            }`}
          >
            <Play className="h-4 w-4 fill-white" /> RUN FDM SIMULATION
          </button>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-4 text-center text-[10px] text-slate-500 border-t border-slate-800">
        <div className="uppercase tracking-wider font-semibold text-slate-400">Radiation Research Platform</div>
        <div className="font-mono text-[9px] mt-0.5 text-slate-500">Bento Grid • FDM Engine v2.4</div>
      </div>
    </aside>
  );
};
