import React, { useState } from 'react';
import { GridData } from '../types';

interface GridMapProps {
  grid: GridData;
  boundaryDose: number;
}

export const GridMap: React.FC<GridMapProps> = ({ grid, boundaryDose }) => {
  const [hovered, setHovered] = useState<{
    x: number;
    y: number;
    type: string;
    dose?: number;
    i: number;
    j: number;
  } | null>(null);

  const { Nx, Ny, xCoords, yCoords, nodeTypes } = grid;

  const width = 480;
  const height = 400;
  const pad = 48;
  const innerW = width - 2 * pad;
  const innerH = height - 2 * pad;

  const xMin = xCoords[0];
  const xMax = xCoords[Nx - 1];
  const yMin = yCoords[0];
  const yMax = yCoords[Ny - 1];

  const scaleX = (x: number) => pad + ((x - xMin) / (xMax - xMin || 1)) * innerW;
  const scaleY = (y: number) => height - pad - ((y - yMin) / (yMax - yMin || 1)) * innerH;

  return (
    <div className="relative rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm text-slate-200">
      <div className="mb-3 flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-bold text-white">Structured Computational Mesh</h3>
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-xs bg-slate-500" /> Boundary ({boundaryDose})
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-indigo-500" /> Interior (Unknown)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rotate-45 bg-amber-400" /> Centre Evaluation Node
          </span>
        </div>
      </div>

      <div className="relative flex justify-center">
        <svg width={width} height={height} className="overflow-visible select-none rounded-lg border border-slate-800/80 bg-[#07090e]">
          {/* Grid background & axes */}
          <rect
            x={pad}
            y={pad}
            width={innerW}
            height={innerH}
            fill="#090d16"
            stroke="#1e293b"
            strokeWidth={1}
          />

          {/* Grid lines */}
          {xCoords.map((x, i) => (
            <line
              key={`vl-${i}`}
              x1={scaleX(x)}
              y1={pad}
              x2={scaleX(x)}
              y2={height - pad}
              stroke="#1e293b"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
          ))}
          {yCoords.map((y, j) => (
            <line
              key={`hl-${j}`}
              x1={pad}
              y1={scaleY(y)}
              x2={width - pad}
              y2={scaleY(y)}
              stroke="#1e293b"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
          ))}

          {/* Axis labels */}
          {xCoords.map((x, i) => (
            <text
              key={`xl-${i}`}
              x={scaleX(x)}
              y={height - pad + 18}
              textAnchor="middle"
              className="text-[11px] fill-slate-400 font-mono"
            >
              {x.toFixed(2)}
            </text>
          ))}
          {yCoords.map((y, j) => (
            <text
              key={`yl-${j}`}
              x={pad - 8}
              y={scaleY(y) + 4}
              textAnchor="end"
              className="text-[11px] fill-slate-400 font-mono"
            >
              {y.toFixed(2)}
            </text>
          ))}

          {/* Nodes */}
          {yCoords.map((y, j) =>
            xCoords.map((x, i) => {
              const type = nodeTypes[j]?.[i] || 'boundary';
              const px = scaleX(x);
              const py = scaleY(y);

              if (type === 'boundary') {
                return (
                  <rect
                    key={`n-${i}-${j}`}
                    x={px - 5}
                    y={py - 5}
                    width={10}
                    height={10}
                    fill="#475569"
                    stroke="#1e293b"
                    strokeWidth={1}
                    className="cursor-pointer transition-transform hover:scale-125"
                    onMouseEnter={() =>
                      setHovered({ x, y, type: 'Boundary Node', dose: boundaryDose, i, j })
                    }
                    onMouseLeave={() => setHovered(null)}
                  />
                );
              } else if (type === 'centre') {
                return (
                  <g
                    key={`n-${i}-${j}`}
                    transform={`translate(${px}, ${py})`}
                    className="cursor-pointer transition-transform hover:scale-125"
                    onMouseEnter={() =>
                      setHovered({ x, y, type: 'Centre Evaluation Node', i, j })
                    }
                    onMouseLeave={() => setHovered(null)}
                  >
                    <polygon
                      points="0,-9 2.5,-3 8.5,-3 4,1 5.5,7 0,3.5 -5.5,7 -4,1 -8.5,-3 -2.5,-3"
                      fill="#f59e0b"
                      stroke="#78350f"
                      strokeWidth={1.5}
                    />
                  </g>
                );
              } else {
                return (
                  <circle
                    key={`n-${i}-${j}`}
                    cx={px}
                    cy={py}
                    r={6}
                    fill="#6366f1"
                    stroke="#312e81"
                    strokeWidth={1.2}
                    className="cursor-pointer transition-transform hover:scale-125"
                    onMouseEnter={() =>
                      setHovered({ x, y, type: 'Interior Unknown Node', i, j })
                    }
                    onMouseLeave={() => setHovered(null)}
                  />
                );
              }
            })
          )}
        </svg>

        {hovered && (
          <div className="absolute top-2 right-2 rounded-lg bg-slate-950/95 border border-slate-700 px-3 py-2 text-xs text-white shadow-xl pointer-events-none font-mono">
            <div className="font-semibold text-indigo-400">{hovered.type}</div>
            <div className="text-slate-300">Index: ({hovered.i}, {hovered.j})</div>
            <div className="text-slate-300">Coordinates: ({hovered.x.toFixed(4)}, {hovered.y.toFixed(4)})</div>
            {hovered.dose !== undefined && <div className="text-emerald-400">Boundary Dose: {hovered.dose}</div>}
          </div>
        )}
      </div>

      <div className="mt-2 text-center text-xs text-slate-500">
        Hover over nodes to inspect Cartesian coordinates and boundary conditions.
      </div>
    </div>
  );
};
