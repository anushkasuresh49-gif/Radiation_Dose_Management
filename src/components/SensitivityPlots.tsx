import React from 'react';
import { SensitivityData } from '../types';

interface SensitivityPlotsProps {
  data: SensitivityData;
}

export const SensitivityPlots: React.FC<SensitivityPlotsProps> = ({ data }) => {
  const renderLineChart = (
    title: string,
    xLabel: string,
    xVals: number[],
    yVals: number[],
    color: string
  ) => {
    const w = 260;
    const h = 180;
    const padL = 45;
    const padR = 20;
    const padT = 20;
    const padB = 35;
    const pw = w - padL - padR;
    const ph = h - padT - padB;

    const minX = Math.min(...xVals);
    const maxX = Math.max(...xVals);
    const minY = Math.min(...yVals, 0);
    const maxY = Math.max(...yVals) * 1.1 || 1;

    const sx = (x: number) => padL + ((x - minX) / (maxX - minX || 1)) * pw;
    const sy = (y: number) => padT + ph - ((y - minY) / (maxY - minY || 1)) * ph;

    const points = xVals.map((xv, i) => `${sx(xv)},${sy(yVals[i])}`).join(' ');

    return (
      <div className="rounded-lg border border-slate-800 bg-[#07090e] p-3.5">
        <div className="text-xs font-bold text-slate-200 mb-2">{title}</div>
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
          {xVals.map((xv, i) => {
            const cx = sx(xv);
            const cy = sy(yVals[i]);
            return (
              <g key={i}>
                <circle cx={cx} cy={cy} r={3.5} fill={color} stroke="#07090e" strokeWidth={1.5} />
                <text
                  x={cx}
                  y={cy - 6}
                  textAnchor="middle"
                  className="text-[9px] fill-slate-300 font-mono font-bold"
                >
                  {yVals[i].toFixed(3)}
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
              {xv}
            </text>
          ))}

          <text
            x={padL + pw / 2}
            y={h - 4}
            textAnchor="middle"
            className="text-[10px] fill-slate-400 font-medium"
          >
            {xLabel}
          </text>
        </svg>
      </div>
    );
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm text-slate-200">
      <h3 className="text-sm font-bold text-white mb-1">
        Parameter Sensitivity Response Curves
      </h3>
      <p className="text-xs text-slate-400 mb-3">
        Parametric variation curves showing response of centre-point dose to physical constants
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {renderLineChart(
          'Diffusion Coeff. (k) vs Dose',
          'Diffusion Coefficient (k)',
          data.kValues,
          data.kDoses,
          '#38bdf8'
        )}
        {renderLineChart(
          'Source Intensity (S) vs Dose',
          'Source Term (S)',
          data.sValues,
          data.sDoses,
          '#f43f5e'
        )}
        {renderLineChart(
          'Grid Spacing (h) vs Dose',
          'Mesh Spacing (h)',
          data.hValues,
          data.hDoses,
          '#a855f7'
        )}
      </div>

      <div className="mt-4 rounded-lg border border-indigo-500/30 bg-indigo-950/20 p-3.5 text-xs text-indigo-300 leading-relaxed">
        <strong className="font-semibold text-indigo-200">Sensitivity Findings:</strong> {data.interpretation}
      </div>
    </div>
  );
};
