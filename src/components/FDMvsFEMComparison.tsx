import React from 'react';
import { FDMSolutionData, FEMSolutionData, ValidationData } from '../types';
import { DoseHeatmap } from './DoseHeatmap';

interface FDMvsFEMComparisonProps {
  fdmSol: FDMSolutionData;
  femSol: FEMSolutionData;
  val: ValidationData;
}

export const FDMvsFEMComparison: React.FC<FDMvsFEMComparisonProps> = ({
  fdmSol,
  femSol,
  val
}) => {
  const absDiff = Math.abs(fdmSol.centreDose - femSol.centreDose);
  const timeRatio =
    fdmSol.executionTimeMs > 0
      ? (femSol.executionTimeMs / fdmSol.executionTimeMs).toFixed(2)
      : '1.0';

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">FDM Centre Dose</span>
          <div className="text-2xl font-bold text-slate-800 mt-1">{fdmSol.centreDose.toFixed(6)}</div>
          <span className="text-xs text-slate-500">{fdmSol.grid.interiorNodesCount} interior unknowns</span>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">FEM Centre Dose</span>
          <div className="text-2xl font-bold text-teal-700 mt-1">{femSol.centreDose.toFixed(6)}</div>
          <span className="text-xs text-slate-500">{femSol.mesh.totalElements} triangular elements</span>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Cross-Solver Delta</span>
          <div className="text-2xl font-bold text-blue-600 mt-1">{absDiff.toExponential(4)}</div>
          <span className="text-xs text-slate-500">|D_FDM - D_FEM|</span>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Continuous Analytical</span>
          <div className="text-2xl font-bold text-indigo-700 mt-1">{val.continuousAnalyticalDose.toFixed(6)}</div>
          <span className="text-xs text-slate-500">2D Fourier Series limit</span>
        </div>
      </div>

      {/* Side-by-Side Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-slate-700">FDM Dose Distribution (5-Point Stencil)</h4>
            <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-medium">FDM Grid</span>
          </div>
          <DoseHeatmap sol={fdmSol} />
        </div>
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-slate-700">FEM Dose Distribution (Triangular Elements)</h4>
            <span className="text-xs px-2 py-0.5 bg-teal-100 text-teal-700 rounded-full font-medium">FEM Variational</span>
          </div>
          {/* Reuse DoseHeatmap with FEM reconstructed matrix */}
          <DoseHeatmap
            sol={{
              ...fdmSol,
              doseMatrix: femSol.doseMatrix,
              centreDose: femSol.centreDose,
              maxDose: femSol.maxDose,
              minDose: femSol.minDose,
              meanDose: femSol.meanDose
            }}
          />
        </div>
      </div>

      {/* Detailed Comparison Table */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs overflow-x-auto">
        <h3 className="text-base font-semibold text-slate-800 mb-3">
          Comprehensive FDM vs FEM Performance Matrix
        </h3>
        <table className="w-full text-xs text-left text-slate-700 border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
              <th className="py-2.5 px-3">Evaluation Metric</th>
              <th className="py-2.5 px-3">Finite Difference (FDM)</th>
              <th className="py-2.5 px-3">Finite Element (FEM)</th>
              <th className="py-2.5 px-3">Comparative Note</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            <tr>
              <td className="py-2.5 px-3 font-medium">Discretization Method</td>
              <td className="py-2.5 px-3">5-point Cartesian Central Difference</td>
              <td className="py-2.5 px-3">3-node Linear Triangular Elements (CST)</td>
              <td className="py-2.5 px-3 text-slate-500">Differential vs Variational formulation</td>
            </tr>
            <tr>
              <td className="py-2.5 px-3 font-medium">Centre-Point Dose D</td>
              <td className="py-2.5 px-3 font-mono font-bold text-slate-800">{fdmSol.centreDose.toFixed(6)}</td>
              <td className="py-2.5 px-3 font-mono font-bold text-teal-700">{femSol.centreDose.toFixed(6)}</td>
              <td className="py-2.5 px-3 text-slate-500">Difference: {absDiff.toExponential(4)}</td>
            </tr>
            <tr>
              <td className="py-2.5 px-3 font-medium">PPT Benchmark (h=0.5) Error</td>
              <td className="py-2.5 px-3 font-mono">{val.fdmVsPptAbsError.toExponential(4)} ({val.fdmVsPptRelErrorPct.toFixed(2)}%)</td>
              <td className="py-2.5 px-3 font-mono">{val.femVsPptAbsError.toExponential(4)} ({val.femVsPptRelErrorPct.toFixed(2)}%)</td>
              <td className="py-2.5 px-3 text-emerald-600 font-medium">Identical result at h=0.5</td>
            </tr>
            <tr>
              <td className="py-2.5 px-3 font-medium">Error vs Continuous Analytical</td>
              <td className="py-2.5 px-3 font-mono">{val.fdmVsAnaAbsError.toFixed(6)} ({val.fdmVsAnaRelErrorPct.toFixed(2)}%)</td>
              <td className="py-2.5 px-3 font-mono">{val.femVsAnaAbsError.toFixed(6)} ({val.femVsAnaRelErrorPct.toFixed(2)}%)</td>
              <td className="py-2.5 px-3 text-slate-500">Asymptotically converges as h → 0</td>
            </tr>
            <tr>
              <td className="py-2.5 px-3 font-medium">Discretization Entities</td>
              <td className="py-2.5 px-3">{fdmSol.grid.totalNodes} total nodes ({fdmSol.grid.interiorNodesCount} interior)</td>
              <td className="py-2.5 px-3">{femSol.mesh.totalElements} triangles, {femSol.mesh.totalNodes} nodes</td>
              <td className="py-2.5 px-3 text-slate-500">FEM captures unstructured geometry</td>
            </tr>
            <tr>
              <td className="py-2.5 px-3 font-medium">Maximum Domain Dose</td>
              <td className="py-2.5 px-3 font-mono">{fdmSol.maxDose.toFixed(6)}</td>
              <td className="py-2.5 px-3 font-mono">{femSol.maxDose.toFixed(6)}</td>
              <td className="py-2.5 px-3 text-slate-500">Peak radiation dose concentration</td>
            </tr>
            <tr>
              <td className="py-2.5 px-3 font-medium">Average Domain Dose</td>
              <td className="py-2.5 px-3 font-mono">{fdmSol.meanDose.toFixed(6)}</td>
              <td className="py-2.5 px-3 font-mono">{femSol.meanDose.toFixed(6)}</td>
              <td className="py-2.5 px-3 text-slate-500">Spatial integral across tissue domain</td>
            </tr>
            <tr>
              <td className="py-2.5 px-3 font-medium">Execution Runtime</td>
              <td className="py-2.5 px-3 font-mono">{fdmSol.executionTimeMs.toFixed(2)} ms</td>
              <td className="py-2.5 px-3 font-mono">{femSol.executionTimeMs.toFixed(2)} ms</td>
              <td className="py-2.5 px-3 text-slate-500">FEM overhead: ~{timeRatio}x (element assembly)</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
