import React, { useState, useMemo } from 'react';
import { FDMSolutionData } from '../types';

interface DoseHeatmapProps {
  sol: FDMSolutionData;
}

// Viridis colormap approximation
function viridisColor(t: number): string {
  const clamped = Math.max(0, Math.min(1, t));
  // 5 control points
  const points = [
    { pos: 0.0, r: 68, g: 1, b: 84 },
    { pos: 0.25, r: 59, g: 82, b: 139 },
    { pos: 0.5, r: 33, g: 145, b: 140 },
    { pos: 0.75, r: 94, g: 201, b: 98 },
    { pos: 1.0, r: 253, g: 231, b: 37 }
  ];

  for (let i = 0; i < points.length - 1; i++) {
    const p1 = points[i];
    const p2 = points[i + 1];
    if (clamped >= p1.pos && clamped <= p2.pos) {
      const frac = (clamped - p1.pos) / (p2.pos - p1.pos);
      const r = Math.round(p1.r + frac * (p2.r - p1.r));
      const g = Math.round(p1.g + frac * (p2.g - p1.g));
      const b = Math.round(p1.b + frac * (p2.b - p1.b));
      return `rgb(${r}, ${g}, ${b})`;
    }
  }
  return 'rgb(253, 231, 37)';
}

export const DoseHeatmap: React.FC<DoseHeatmapProps> = ({ sol }) => {
  const { grid, doseMatrix, centreDose, minDose, maxDose } = sol;
  const { Nx, Ny, xCoords, yCoords, centreIndex } = grid;

  const [hovered, setHovered] = useState<{
    x: number;
    y: number;
    dose: number;
    i: number;
    j: number;
  } | null>(null);

  const width = 500;
  const height = 420;
  const padL = 50;
  const padR = 80;
  const padT = 30;
  const padB = 45;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;

  const xMin = xCoords[0];
  const xMax = xCoords[Nx - 1];
  const yMin = yCoords[0];
  const yMax = yCoords[Ny - 1];

  const scaleX = (x: number) => padL + ((x - xMin) / (xMax - xMin || 1)) * plotW;
  const scaleY = (y: number) => padT + plotH - ((y - yMin) / (yMax - yMin || 1)) * plotH;

  const doseRange = maxDose - minDose || 1;

  // Cells
  const cells = useMemo(() => {
    const list: {
      key: string;
      x: number;
      y: number;
      w: number;
      h: number;
      color: string;
      dose: number;
      i: number;
      j: number;
    }[] = [];

    const dx = plotW / (Nx - 1 || 1);
    const dy = plotH / (Ny - 1 || 1);

    for (let j = 0; j < Ny; j++) {
      for (let i = 0; i < Nx; i++) {
        const val = doseMatrix[j][i];
        const norm = (val - minDose) / doseRange;
        const color = viridisColor(norm);
        const cx = scaleX(xCoords[i]);
        const cy = scaleY(yCoords[j]);

        list.push({
          key: `${i}-${j}`,
          x: cx - dx / 2,
          y: cy - dy / 2,
          w: dx,
          h: dy,
          color,
          dose: val,
          i,
          j
        });
      }
    }
    return list;
  }, [Nx, Ny, doseMatrix, minDose, maxDose, plotW, plotH]);

  const [ci, cj] = centreIndex;
  const centrePx = scaleX(xCoords[ci]);
  const centrePy = scaleY(yCoords[cj]);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm text-slate-200">
      <div className="mb-2 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white">2D Radiation Dose Distribution Heatmap</h3>
          <p className="text-xs text-slate-400">Spatial absorbed dose field across computational domain</p>
        </div>
        <div className="text-right text-xs text-slate-400 font-mono">
          <div>Max: {maxDose.toFixed(4)} Gy/unit</div>
          <div>Min: {minDose.toFixed(4)} Gy/unit</div>
        </div>
      </div>

      <div className="relative flex justify-center">
        <svg width={width} height={height} className="select-none overflow-visible rounded-lg border border-slate-800/80 bg-[#07090e]">
          {/* Heatmap cells */}
          <g>
            {cells.map((c) => (
              <rect
                key={c.key}
                x={c.x}
                y={c.y}
                width={c.w}
                height={c.h}
                fill={c.color}
                stroke="#1e293b"
                strokeWidth={0.2}
                className="cursor-crosshair transition-opacity hover:opacity-80"
                onMouseEnter={() =>
                  setHovered({
                    x: xCoords[c.i],
                    y: yCoords[c.j],
                    dose: c.dose,
                    i: c.i,
                    j: c.j
                  })
                }
                onMouseLeave={() => setHovered(null)}
              />
            ))}
          </g>

          {/* Centre marker */}
          <g transform={`translate(${centrePx}, ${centrePy})`}>
            <circle r={8} fill="none" stroke="#ffffff" strokeWidth={2.5} />
            <circle r={8} fill="none" stroke="#ef4444" strokeWidth={1.5} />
            <line x1={-12} y1={0} x2={12} y2={0} stroke="#ef4444" strokeWidth={2} />
            <line x1={0} y1={-12} x2={0} y2={12} stroke="#ef4444" strokeWidth={2} />
            <circle r={2.5} fill="#ffffff" />
          </g>

          {/* Colorbar */}
          <g transform={`translate(${width - 45}, ${padT})`}>
            <text x={0} y={-10} className="text-[10px] fill-slate-400 font-semibold">
              Dose D
            </text>
            {Array.from({ length: 100 }, (_, idx) => {
              const t = (99 - idx) / 99;
              return (
                <rect
                  key={`cb-${idx}`}
                  x={0}
                  y={(idx / 100) * plotH}
                  width={14}
                  height={plotH / 100 + 0.5}
                  fill={viridisColor(t)}
                />
              );
            })}
            <rect x={0} y={0} width={14} height={plotH} fill="none" stroke="#475569" strokeWidth={1} />
            <text x={18} y={10} className="text-[10px] fill-slate-400 font-mono">
              {maxDose.toFixed(3)}
            </text>
            <text x={18} y={plotH / 2 + 4} className="text-[10px] fill-slate-400 font-mono">
              {((maxDose + minDose) / 2).toFixed(3)}
            </text>
            <text x={18} y={plotH - 2} className="text-[10px] fill-slate-400 font-mono">
              {minDose.toFixed(3)}
            </text>
          </g>

          {/* Axis Labels */}
          {xCoords.map((x, i) => (
            <text
              key={`xl-${i}`}
              x={scaleX(x)}
              y={padT + plotH + 18}
              textAnchor="middle"
              className="text-[10px] fill-slate-400 font-mono"
            >
              {x.toFixed(2)}
            </text>
          ))}
          {yCoords.map((y, j) => (
            <text
              key={`yl-${j}`}
              x={padL - 8}
              y={scaleY(y) + 3}
              textAnchor="end"
              className="text-[10px] fill-slate-400 font-mono"
            >
              {y.toFixed(2)}
            </text>
          ))}

          <text
            x={padL + plotW / 2}
            y={height - 8}
            textAnchor="middle"
            className="text-xs fill-slate-300 font-medium"
          >
            Spatial Coordinate X
          </text>
          <text
            x={14}
            y={padT + plotH / 2}
            textAnchor="middle"
            transform={`rotate(-90 14 ${padT + plotH / 2})`}
            className="text-xs fill-slate-300 font-medium"
          >
            Spatial Coordinate Y
          </text>
        </svg>

        {hovered && (
          <div className="absolute top-2 left-16 rounded-lg bg-slate-950/95 border border-slate-700 px-3 py-2 text-xs text-white shadow-xl pointer-events-none font-mono">
            <div className="font-semibold text-indigo-400">Position ({hovered.x.toFixed(4)}, {hovered.y.toFixed(4)})</div>
            <div className="text-slate-300">Grid Index: [{hovered.j}, {hovered.i}]</div>
            <div className="text-sm font-bold text-amber-400">Dose D: {hovered.dose.toFixed(6)}</div>
          </div>
        )}
      </div>

      <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
        <span>Red crosshairs indicate domain centre point.</span>
        <span className="font-semibold text-indigo-400 font-mono">Centre Dose: {centreDose.toFixed(6)}</span>
      </div>
    </div>
  );
};
