import React from 'react';
import { FDMSolutionData, FEMSolutionData, ValidationData, TumourMetrics, ModelParams } from '../types';
import { FileSpreadsheet, Download, CheckCircle2, Info } from 'lucide-react';

interface ReportViewProps {
  sol: FDMSolutionData;
  femSol: FEMSolutionData;
  val: ValidationData;
  tumour: TumourMetrics;
  params: ModelParams;
}

export const ReportView: React.FC<ReportViewProps> = ({
  sol,
  femSol,
  val,
  tumour,
  params: p
}) => {
  const handleDownloadCSV = () => {
    let csv = '# OPTIMISING RADIATION DOSE DISTRIBUTION IN CANCER TREATMENT\n';
    csv += '# Using Finite Difference and Finite Element Methods\n';
    csv += `# Generated: ${new Date().toISOString()}\n`;
    csv += '# Academic Research Capstone Project - Not for clinical use\n\n';

    csv += 'Category,Parameter,Value\n';
    csv += `Domain,Spatial X Range,[${p.xmin} ${p.xmax}] (Lx=${p.xmax - p.xmin})\n`;
    csv += `Domain,Spatial Y Range,[${p.ymin} ${p.ymax}] (Ly=${p.ymax - p.ymin})\n`;
    csv += `Domain,Grid Spacing (h),${p.h}\n`;
    csv += `Domain,Total Grid Points,${sol.grid.totalNodes}\n`;
    csv += `Domain,Interior Unknowns,${sol.grid.interiorNodesCount}\n`;
    csv += `Model,Diffusion Coeff (k),${p.k}\n`;
    csv += `Model,Source Intensity (S),${p.S}\n`;
    csv += `Model,Boundary Dose (Db),${p.boundaryDose}\n`;

    csv += `FDM Solver,Centre-Point Dose,${sol.centreDose.toFixed(6)}\n`;
    csv += `FDM Solver,Maximum Dose,${sol.maxDose.toFixed(6)}\n`;
    csv += `FDM Solver,Minimum Dose,${sol.minDose.toFixed(6)}\n`;
    csv += `FDM Solver,Mean Dose,${sol.meanDose.toFixed(6)}\n`;
    csv += `FDM Solver,Execution Time (ms),${sol.executionTimeMs.toFixed(3)}\n`;

    csv += `FEM Solver,Centre-Point Dose,${femSol.centreDose.toFixed(6)}\n`;
    csv += `FEM Solver,Triangular Elements,${femSol.mesh.totalElements}\n`;
    csv += `FEM Solver,Maximum Dose,${femSol.maxDose.toFixed(6)}\n`;
    csv += `FEM Solver,Minimum Dose,${femSol.minDose.toFixed(6)}\n`;
    csv += `FEM Solver,Execution Time (ms),${femSol.executionTimeMs.toFixed(3)}\n`;

    csv += `Validation,PPT Benchmark (h=0.5),${val.pptBenchmark.toFixed(6)}\n`;
    csv += `Validation,FDM vs PPT Error,${val.fdmVsPptAbsError.toExponential(4)}\n`;
    csv += `Validation,FEM vs PPT Error,${val.femVsPptAbsError.toExponential(4)}\n`;
    csv += `Validation,Continuous Fourier Analytical,${val.continuousAnalyticalDose.toFixed(6)}\n`;
    csv += `Validation,FDM vs Analytical Error,${val.fdmVsAnaAbsError.toFixed(6)}\n`;
    csv += `Validation,FEM vs Analytical Error,${val.femVsAnaAbsError.toFixed(6)}\n`;

    csv += `Exposure,Avg Tumour Dose,${tumour.avgTumourDose.toFixed(6)}\n`;
    csv += `Exposure,Avg Surrounding Dose,${tumour.avgSurroundingDose.toFixed(6)}\n`;
    csv += `Exposure,Tumour/Surrounding Ratio,${tumour.tumourToSurroundingRatio.toFixed(2)}\n\n`;

    csv += '## 2D FDM DOSE DISTRIBUTION MATRIX\n';
    csv += ',' + sol.grid.xCoords.join(',') + '\n';
    for (let j = 0; j < sol.grid.Ny; j++) {
      csv += `${sol.grid.yCoords[j]},` + sol.doseMatrix[j].map(v => v.toFixed(6)).join(',') + '\n';
    }

    csv += '\n## 2D FEM DOSE DISTRIBUTION MATRIX\n';
    csv += ',' + sol.grid.xCoords.join(',') + '\n';
    for (let j = 0; j < femSol.mesh.Ny; j++) {
      csv += `${sol.grid.yCoords[j]},` + femSol.doseMatrix[j].map(v => v.toFixed(6)).join(',') + '\n';
    }

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `FDM_FEM_Radiation_Dose_Report_h${p.h}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const rows = [
    { cat: 'Spatial Domain', param: 'X Range [xmin, xmax]', val: `[${p.xmin}, ${p.xmax}] (Lx=${p.xmax - p.xmin})` },
    { cat: 'Spatial Domain', param: 'Y Range [ymin, ymax]', val: `[${p.ymin}, ${p.ymax}] (Ly=${p.ymax - p.ymin})` },
    { cat: 'Discretization', param: 'Mesh Spacing (h)', val: `${p.h}` },
    { cat: 'Discretization', param: 'FDM Grid Nodes', val: `${sol.grid.totalNodes} (${sol.grid.interiorNodesCount} interior)` },
    { cat: 'Discretization', param: 'FEM Triangular Elements', val: `${femSol.mesh.totalElements} triangles (${femSol.mesh.totalNodes} nodes)` },
    { cat: 'Model Physics', param: 'Diffusion Coefficient (k)', val: `${p.k}` },
    { cat: 'Model Physics', param: 'Source Intensity (S)', val: `${p.S}` },
    { cat: 'Model Physics', param: 'Dirichlet Boundary Dose', val: `${p.boundaryDose}` },
    { cat: 'FDM Solution', param: 'FDM Centre Dose', val: `${sol.centreDose.toFixed(6)}` },
    { cat: 'FDM Solution', param: 'FDM Max / Min Dose', val: `${sol.maxDose.toFixed(6)} / ${sol.minDose.toFixed(6)}` },
    { cat: 'FDM Solution', param: 'FDM Execution Time', val: `${sol.executionTimeMs.toFixed(3)} ms` },
    { cat: 'FEM Solution', param: 'FEM Centre Dose', val: `${femSol.centreDose.toFixed(6)}` },
    { cat: 'FEM Solution', param: 'FEM Max / Min Dose', val: `${femSol.maxDose.toFixed(6)} / ${femSol.minDose.toFixed(6)}` },
    { cat: 'FEM Solution', param: 'FEM Execution Time', val: `${femSol.executionTimeMs.toFixed(3)} ms` },
    { cat: 'Validation', param: 'PPT Benchmark (h=0.5)', val: `${val.pptBenchmark.toFixed(6)}` },
    { cat: 'Validation', param: 'FDM Error vs PPT Benchmark', val: `${val.fdmVsPptAbsError.toExponential(4)} (${val.fdmVsPptRelErrorPct.toFixed(2)}%)` },
    { cat: 'Validation', param: 'FEM Error vs PPT Benchmark', val: `${val.femVsPptAbsError.toExponential(4)} (${val.femVsPptRelErrorPct.toFixed(2)}%)` },
    { cat: 'Validation', param: 'Continuous Fourier Analytical', val: `${val.continuousAnalyticalDose.toFixed(6)}` },
    { cat: 'Validation', param: 'FDM Error vs Continuous', val: `${val.fdmVsAnaAbsError.toFixed(6)} (${val.fdmVsAnaRelErrorPct.toFixed(2)}%)` },
    { cat: 'Validation', param: 'FEM Error vs Continuous', val: `${val.femVsAnaAbsError.toFixed(6)} (${val.femVsAnaRelErrorPct.toFixed(2)}%)` },
    { cat: 'Tissue Exposure', param: 'Mean Tumour Dose', val: `${tumour.avgTumourDose.toFixed(6)}` },
    { cat: 'Tissue Exposure', param: 'Mean Healthy Surrounding Dose', val: `${tumour.avgSurroundingDose.toFixed(6)}` },
    { cat: 'Tissue Exposure', param: 'Tumour / Surrounding Selectivity', val: `${tumour.tumourToSurroundingRatio.toFixed(2)}×` }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
        <div>
          <h2 className="text-base font-bold text-slate-800">Academic Research Simulation Report</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Export dual-solver mathematical validation data, comparative matrices, and formal documentation
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer shadow-xs transition-colors"
          >
            <FileSpreadsheet className="h-4 w-4 text-emerald-600" /> Export CSV Data
          </button>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-700 cursor-pointer shadow-xs transition-colors"
          >
            <Download className="h-4 w-4" /> Print / Save PDF
          </button>
        </div>
      </div>

      {/* Primary Summary Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="border-b border-slate-200 bg-slate-50/80 px-5 py-3">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Comparative Simulation Parameter & Performance Table
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="border-b border-slate-200 bg-slate-50/40 text-[11px] font-semibold text-slate-500 uppercase">
              <tr>
                <th className="px-5 py-2.5">Category</th>
                <th className="px-5 py-2.5">Parameter Description</th>
                <th className="px-5 py-2.5 font-mono">Calculated Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r, i) => (
                <tr key={i} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-5 py-2 font-medium text-slate-500">{r.cat}</td>
                  <td className="px-5 py-2 font-medium text-slate-800">{r.param}</td>
                  <td className="px-5 py-2 font-mono font-semibold text-blue-700">{r.val}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Academic Interpretation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5 shadow-xs text-xs">
          <h3 className="font-semibold text-emerald-900 flex items-center gap-1.5 mb-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Academic Mathematical Verification
          </h3>
          <p className="text-slate-700 leading-relaxed">
            Both Finite Difference (FDM) and Finite Element (FEM) methods solve the elliptic Poisson equation -k∇²D = S.
            For the canonical PPT benchmark ($L_x=1, L_y=1, k=1, S=4, h=0.5, D_b=0$):
          </p>
          <div className="my-2.5 rounded-lg bg-white border border-emerald-200 p-2.5 font-mono text-[11px] text-emerald-800">
            FDM Centre Dose = 0.250000 | FEM Centre Dose = 0.250000
          </div>
          <p className="text-slate-700 leading-relaxed">
            Both solvers achieve 0.000000 absolute error against the benchmark formulation, validating the linear system assembly and element integration logic.
          </p>
        </div>

        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-5 shadow-xs text-xs">
          <h3 className="font-semibold text-blue-900 flex items-center gap-1.5 mb-2">
            <Info className="h-4 w-4 text-blue-600" /> Scientific Discussion & Sparing Healthy Tissue
          </h3>
          <ul className="list-disc pl-4 space-y-1.5 text-slate-700">
            <li>
              <strong>Cross-Solver Confirmation:</strong> FDM and FEM yield congruent spatial distributions while highlighting FEM&apos;s natural adaptability to complex anatomical contours.
            </li>
            <li>
              <strong>Target Concentration:</strong> High source intensity S coupled with boundary zero conditions produces strong central dose confinement.
            </li>
            <li>
              <strong>Academic Disclaimer:</strong> Demonstrates numerical methodology for cancer therapy dose optimization; not for clinical radiotherapy prescription.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
