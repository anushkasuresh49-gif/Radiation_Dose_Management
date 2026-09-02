import React from 'react';
import { ConvergenceItem } from '../types';

interface ConvergencePlotsProps {
  data: ConvergenceItem[];
}

export const ConvergencePlots: React.FC<ConvergencePlotsProps> = ({ data }) => {
  if (!data || data.length === 0) return null;

  // Render 4 subplots:
  // 1: Grid spacing h vs Centre Dose
  // 2: Grid spacing h vs Absolute Error
  // 3: Grid spacing h vs Relative Error (%)
  // 4: Grid spacing h vs Execution Time (ms)

  const sorted = [...data].sort((a, b) => a.h - b.h);

  const renderMiniChart = (
    title: string,
    yLabel: string,
    getValue: (d: ConvergenceItem) => number,
    formatVal: (v: number) => string,
    color: string
  ) => {
    const w = 260;
    const h = 170;
    const padL = 45;
    const padR = 20;
    const padT = 20;
    const padB = 30;
    const pw = w - padL - padR;
    const ph = h - padT - padB;

    const xVals = sorted.map((d) => d.h);
    const yVals = sorted.map(getValue);

    const minX = Math.min(...xVals);
    const maxX = Math.max(...xVals);
    const minY = Math.min(...yVals, 0);
    const maxY = Math.max(...yVals) * 1.1 || 1;

    const sx = (x: number) => padL + ((x - minX) / (maxX - minX || 1)) * pw;
    const sy = (y: number) => padT + ph - ((y - minY) / (maxY - minY || 1)) * ph;

    const points = sorted.map((d) => `${sx(d.h)},${sy(getValue(d))}`).join(' ');

    return (
      <div className="rounded-lg border border-slate-800 bg-[#07090e] p-3.5">
        <div className="text-xs font-bold text-slate-200 mb-2 flex items-center justify-between">
          <span>{title}</span>
          <span className="text-[10px] text-slate-400 font-mono">{yLabel}</span>
        </div>
        <svg width={w} height={h} className="select-none overflow-visible">
          {/* Axes */}
          <line x1={padL} y1={padT} x2={padL} y2={padT + ph} stroke="#1e293b" strokeWidth={1} />
          <line
            x1={padL}
            y1={padT + ph}
            x2={padL + pw}
            y2={padT + ph}
            stroke="#1e293b"
            strokeWidth={1}
          />

          {/* Polyline */}
          <polyline
            fill="none"
            stroke={color}
            strokeWidth={2}
            points={points}
            strokeLinejoin="round"
          />

          {/* Data dots */}
          {sorted.map((d, i) => {
            const cx = sx(d.h);
            const cy = sy(getValue(d));
            return (
              <g key={i}>
                <circle cx={cx} cy={cy} r={4} fill={color} stroke="#07090e" strokeWidth={1.5} />
                <text
                  x={cx}
                  y={cy - 7}
                  textAnchor="middle"
                  className="text-[9px] fill-slate-300 font-mono font-bold"
                >
                  {formatVal(getValue(d))}
                </text>
              </g>
            );
          })}

          {/* X ticks */}
          {xVals.map((xv, i) => (
            <text
              key={i}
              x={sx(xv)}
              y={padT + ph + 14}
              textAnchor="middle"
              className="text-[9px] fill-slate-400 font-mono"
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
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm text-slate-200">
      <h3 className="text-sm font-bold text-white mb-1">
        Grid Refinement Multi-Panel Analysis
      </h3>
      <p className="text-xs text-slate-400 mb-3">
        Asymptotic convergence behavior and computational complexity scaling as h → 0
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {renderMiniChart(
          '1. Spacing (h) vs Centre Dose',
          'Dose',
          (d) => d.centreDose,
          (v) => v.toFixed(4),
          '#6366f1'
        )}
        {renderMiniChart(
          '2. Spacing (h) vs Absolute Error',
          'Abs Error',
          (d) => d.absoluteError,
          (v) => (v < 1e-4 ? v.toExponential(2) : v.toFixed(4)),
          '#f43f5e'
        )}
        {renderMiniChart(
          '3. Spacing (h) vs Relative Error (%)',
          'Rel Error %',
          (d) => d.relativeErrorPct,
          (v) => `${v.toFixed(2)}%`,
          '#f59e0b'
        )}
        {renderMiniChart(
          '4. Spacing (h) vs Execution Time (ms)',
          'Time (ms)',
          (d) => d.executionTimeMs,
          (v) => `${v.toFixed(2)}ms`,
          '#10b981'
        )}
      </div>
    </div>
  );
};
