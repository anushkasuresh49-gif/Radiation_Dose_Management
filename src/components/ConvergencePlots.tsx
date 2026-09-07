import React from 'react';
import { ConvergenceItem } from '../types';

interface ConvergencePlotsProps {
  data: ConvergenceItem[];
}

export const ConvergencePlots: React.FC<ConvergencePlotsProps> = ({ data }) => {
  if (!data || data.length === 0) return null;

  const sorted = [...data].sort((a, b) => a.h - b.h);

  const renderDualChart = (
    title: string,
    yLabel: string,
    getFdm: (d: ConvergenceItem) => number,
    getFem: (d: ConvergenceItem) => number,
    getRef?: (d: ConvergenceItem) => number,
    formatVal: (v: number) => string = (v) => v.toFixed(4)
  ) => {
    const w = 270;
    const h = 180;
    const padL = 45;
    const padR = 20;
    const padT = 20;
    const padB = 35;
    const pw = w - padL - padR;
    const ph = h - padT - padB;

    const xVals = sorted.map((d) => d.h);
    const fdmVals = sorted.map(getFdm);
    const femVals = sorted.map(getFem);
    const refVals = getRef ? sorted.map(getRef) : [];

    const allY = [...fdmVals, ...femVals, ...refVals];
    const minX = Math.min(...xVals);
    const maxX = Math.max(...xVals);
    const minY = Math.min(...allY, 0);
    const maxY = Math.max(...allY) * 1.08 || 1;

    const sx = (x: number) => padL + ((x - minX) / (maxX - minX || 1)) * pw;
    const sy = (y: number) => padT + ph - ((y - minY) / (maxY - minY || 1)) * ph;

    const fdmPoints = sorted.map((d) => `${sx(d.h)},${sy(getFdm(d))}`).join(' ');
    const femPoints = sorted.map((d) => `${sx(d.h)},${sy(getFem(d))}`).join(' ');
    const refPoints = getRef ? sorted.map((d) => `${sx(d.h)},${sy(getRef(d))}`).join(' ') : '';

    return (
      <div className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-xs">
        <div className="text-xs font-bold text-slate-800 mb-1.5 flex items-center justify-between">
          <span>{title}</span>
          <span className="text-[10px] text-slate-500 font-mono">{yLabel}</span>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-slate-600 mb-2">
          <span className="inline-flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-600 inline-block"></span> FDM
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-teal-600 inline-block"></span> FEM
          </span>
          {getRef && (
            <span className="inline-flex items-center gap-1">
              <span className="w-2 h-0.5 bg-rose-500 inline-block"></span> Exact Ref
            </span>
          )}
        </div>

        <svg width={w} height={h} className="select-none overflow-visible">
          {/* Axes */}
          <line x1={padL} y1={padT} x2={padL} y2={padT + ph} stroke="#cbd5e1" strokeWidth={1} />
          <line x1={padL} y1={padT + ph} x2={padL + pw} y2={padT + ph} stroke="#cbd5e1" strokeWidth={1} />

          {/* Reference line */}
          {getRef && (
            <polyline
              fill="none"
              stroke="#ef4444"
              strokeWidth={1.5}
              strokeDasharray="4,3"
              points={refPoints}
            />
          )}

          {/* FDM Polyline */}
          <polyline
            fill="none"
            stroke="#2563eb"
            strokeWidth={2}
            points={fdmPoints}
            strokeLinejoin="round"
          />

          {/* FEM Polyline */}
          <polyline
            fill="none"
            stroke="#0d9488"
            strokeWidth={2}
            points={femPoints}
            strokeLinejoin="round"
          />

          {/* FDM points */}
          {sorted.map((d, i) => {
            const cx = sx(d.h);
            const cy = sy(getFdm(d));
            return (
              <circle key={`fdm-${i}`} cx={cx} cy={cy} r={3.5} fill="#2563eb" stroke="#ffffff" strokeWidth={1} />
            );
          })}

          {/* FEM points */}
          {sorted.map((d, i) => {
            const cx = sx(d.h);
            const cy = sy(getFem(d));
            return (
              <rect
                key={`fem-${i}`}
                x={cx - 3}
                y={cy - 3}
                width={6}
                height={6}
                fill="#0d9488"
                stroke="#ffffff"
                strokeWidth={1}
              />
            );
          })}

          {/* X ticks */}
          {xVals.map((xv, i) => (
            <text
              key={i}
              x={sx(xv)}
              y={padT + ph + 14}
              textAnchor="middle"
              className="text-[9px] fill-slate-500 font-mono font-medium"
            >
              h={xv}
            </text>
          ))}

          {/* Y Min / Max ticks */}
          <text
            x={padL - 6}
            y={padT + 8}
            textAnchor="end"
            className="text-[9px] fill-slate-400 font-mono"
          >
            {formatVal(maxY)}
          </text>
          <text
            x={padL - 6}
            y={padT + ph}
            textAnchor="end"
            className="text-[9px] fill-slate-400 font-mono"
          >
            {formatVal(minY)}
          </text>
        </svg>
      </div>
    );
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-5 shadow-xs">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-800">
          Dual Solver Mesh Refinement & Convergence Curves
        </h3>
        <p className="text-xs text-slate-500">
          Cross-evaluating Finite Difference (FDM) and Finite Element (FEM) convergence behavior against continuous 2D Fourier series solution
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {renderDualChart(
          '1. Spacing (h) vs Centre Dose',
          'Dose D',
          (d) => d.fdmCentreDose,
          (d) => d.femCentreDose,
          (d) => d.referenceDose,
          (v) => v.toFixed(4)
        )}
        {renderDualChart(
          '2. Spacing (h) vs Absolute Error',
          '|D - D_exact|',
          (d) => d.fdmAbsError,
          (d) => d.femAbsError,
          undefined,
          (v) => (v < 1e-4 ? v.toExponential(2) : v.toFixed(4))
        )}
        {renderDualChart(
          '3. Spacing (h) vs Relative Error (%)',
          'Rel %',
          (d) => d.fdmRelErrorPct,
          (d) => d.femRelErrorPct,
          undefined,
          (v) => `${v.toFixed(2)}%`
        )}
        {renderDualChart(
          '4. Spacing (h) vs Execution Runtime',
          'Time (ms)',
          (d) => d.fdmTimeMs,
          (d) => d.femTimeMs,
          undefined,
          (v) => `${v.toFixed(1)}ms`
        )}
      </div>
    </div>
  );
};
