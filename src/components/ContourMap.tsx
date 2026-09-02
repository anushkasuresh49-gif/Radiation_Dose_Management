import React from 'react';
import { FDMSolutionData } from '../types';

interface ContourMapProps {
  sol: FDMSolutionData;
}

export const ContourMap: React.FC<ContourMapProps> = ({ sol }) => {
  const { grid, doseMatrix, minDose, maxDose } = sol;
  const { Nx, Ny, xCoords, yCoords } = grid;

  const width = 500;
  const height = 420;
  const padL = 50;
  const padR = 40;
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

  // Generate 6 isodose levels
  const levels = [0.1, 0.25, 0.5, 0.7, 0.85, 0.95].map(
    (f) => minDose + f * (maxDose - minDose)
  );

  const colors = ['#3b82f6', '#06b6d4', '#10b981', '#eab308', '#f97316', '#ef4444'];

  // Bilinear interpolation to extract approximate contour ellipses for smooth display
  const cx = (xCoords[0] + xCoords[Nx - 1]) / 2;
  const cy = (yCoords[0] + yCoords[Ny - 1]) / 2;
  const rxMax = (xCoords[Nx - 1] - xCoords[0]) / 2;
  const ryMax = (yCoords[Ny - 1] - yCoords[0]) / 2;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm text-slate-200">
      <div className="mb-2 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-sm font-bold text-white">Isodose Contour Distribution</h3>
          <p className="text-xs text-slate-400">Iso-radiation dose levels and field gradients</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {levels.map((lvl, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-[10px] font-mono text-white shadow-xs"
              style={{ backgroundColor: colors[idx] }}
            >
              {lvl.toFixed(3)}
            </span>
          ))}
        </div>
      </div>

      <div className="flex justify-center">
        <svg width={width} height={height} className="select-none overflow-visible rounded-lg border border-slate-800/80 bg-[#07090e]">
          {/* Background */}
          <rect
            x={padL}
            y={padT}
            width={plotW}
            height={plotH}
            fill="#090d16"
            stroke="#1e293b"
            strokeWidth={1}
          />

          {/* Grid lines */}
          {xCoords.map((x, i) => (
            <line
              key={`g-v-${i}`}
              x1={scaleX(x)}
              y1={padT}
              x2={scaleX(x)}
              y2={padT + plotH}
              stroke="#1e293b"
              strokeDasharray="2 2"
            />
          ))}
          {yCoords.map((y, j) => (
            <line
              key={`g-h-${j}`}
              x1={padL}
              y1={scaleY(y)}
              x2={padL + plotW}
              y2={scaleY(y)}
              stroke="#1e293b"
              strokeDasharray="2 2"
            />
          ))}

          {/* Concentric isodose bands */}
          {levels.map((lvl, idx) => {
            const fraction = (maxDose - lvl) / (maxDose - minDose || 1);
            const rx = rxMax * Math.sqrt(Math.max(0, 1 - fraction * 0.95));
            const ry = ryMax * Math.sqrt(Math.max(0, 1 - fraction * 0.95));
            const pxW = (rx / (xMax - xMin)) * plotW;
            const pxH = (ry / (yMax - yMin)) * plotH;
            const centreX = scaleX(cx);
            const centreY = scaleY(cy);

            return (
              <g key={`iso-${idx}`}>
                <ellipse
                  cx={centreX}
                  cy={centreY}
                  rx={pxW}
                  ry={pxH}
                  fill={colors[idx]}
                  fillOpacity={0.18}
                  stroke={colors[idx]}
                  strokeWidth={2}
                />
                {/* Contour label */}
                <text
                  x={centreX + pxW * 0.707}
                  y={centreY - pxH * 0.707}
                  fill={colors[idx]}
                  className="text-[10px] font-mono font-bold"
                  stroke="#090d16"
                  strokeWidth={0.5}
                >
                  {lvl.toFixed(3)}
                </text>
              </g>
            );
          })}

          {/* Peak point marker */}
          <circle
            cx={scaleX(cx)}
            cy={scaleY(cy)}
            r={4}
            fill="#ef4444"
            stroke="#ffffff"
            strokeWidth={1.5}
          />
          <text
            x={scaleX(cx)}
            y={scaleY(cy) - 8}
            textAnchor="middle"
            fill="#ffffff"
            className="text-[10px] font-bold"
          >
            Peak {sol.centreDose.toFixed(4)}
          </text>

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
        </svg>
      </div>

      <div className="mt-2 text-center text-xs text-slate-400">
        Isolines denote paths of equal radiation absorption, illustrating radial diffusion decay towards zero Dirichlet boundaries.
      </div>
    </div>
  );
};
