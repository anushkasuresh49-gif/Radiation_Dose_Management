import React, { useState } from 'react';
import { FEMMesh, FEMSolutionData } from '../types';

interface FEMMeshPlotProps {
  mesh: FEMMesh;
  femSol?: FEMSolutionData;
}

export const FEMMeshPlot: React.FC<FEMMeshPlotProps> = ({ mesh, femSol }) => {
  const [hoveredNode, setHoveredNode] = useState<{ id: number; x: number; y: number; dose?: number } | null>(null);
  const [hoveredElement, setHoveredElement] = useState<number | null>(null);

  const padding = 45;
  const svgWidth = 520;
  const svgHeight = 520;
  const plotSize = svgWidth - 2 * padding;

  const minX = Math.min(...mesh.nodes.map(n => n[0]));
  const maxX = Math.max(...mesh.nodes.map(n => n[0]));
  const minY = Math.min(...mesh.nodes.map(n => n[1]));
  const maxY = Math.max(...mesh.nodes.map(n => n[1]));

  const toSvgX = (x: number) => padding + ((x - minX) / (maxX - minX || 1)) * plotSize;
  const toSvgY = (y: number) => svgHeight - padding - ((y - minY) / (maxY - minY || 1)) * plotSize;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-base font-semibold text-slate-800">
            Triangular Finite Element Mesh (2D Linear CST Elements)
          </h3>
          <p className="text-xs text-slate-500">
            {mesh.totalElements} triangular elements, {mesh.totalNodes} total nodes ({mesh.interiorNodesCount} interior, {mesh.boundaryNodesCount} boundary)
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 bg-slate-400 rounded-xs inline-block"></span> Boundary Node
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 bg-teal-600 rounded-full inline-block"></span> Interior Node
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 bg-amber-500 rounded-full inline-block"></span> Centre Node
          </span>
        </div>
      </div>

      <div className="relative flex justify-center items-center bg-slate-50/50 rounded-lg p-2 border border-slate-100">
        <svg width={svgWidth} height={svgHeight} className="overflow-visible select-none">
          {/* Elements (triangles) */}
          {mesh.elements.map(elem => {
            const [v1, v2, v3] = elem.vertices;
            const pointsStr = `${toSvgX(v1[0])},${toSvgY(v1[1])} ${toSvgX(v2[0])},${toSvgY(v2[1])} ${toSvgX(v3[0])},${toSvgY(v3[1])}`;
            const isHovered = hoveredElement === elem.id;

            return (
              <polygon
                key={elem.id}
                points={pointsStr}
                fill={isHovered ? 'rgba(14, 165, 233, 0.25)' : 'rgba(241, 245, 249, 0.6)'}
                stroke={isHovered ? '#0284c7' : '#94a3b8'}
                strokeWidth={isHovered ? 1.8 : 0.9}
                className="transition-colors cursor-pointer"
                onMouseEnter={() => setHoveredElement(elem.id)}
                onMouseLeave={() => setHoveredElement(null)}
              />
            );
          })}

          {/* Nodes */}
          {mesh.nodes.map(([x, y], idx) => {
            const sx = toSvgX(x);
            const sy = toSvgY(y);
            const isBoundary = mesh.isBoundary[idx];
            const isCentre = idx === mesh.centreNodeIndex;
            const doseVal = femSol ? femSol.nodalDoses[idx] : undefined;

            let fill = isBoundary ? '#64748b' : '#0d9488';
            let radius = isBoundary ? 4.5 : 5.5;

            if (isCentre) {
              fill = '#f59e0b';
              radius = 7.5;
            }

            return (
              <g key={idx}>
                {isBoundary ? (
                  <rect
                    x={sx - 4}
                    y={sy - 4}
                    width={8}
                    height={8}
                    fill={fill}
                    stroke="#1e293b"
                    strokeWidth={1}
                    className="cursor-pointer hover:scale-125 transition-transform"
                    onMouseEnter={() => setHoveredNode({ id: idx, x, y, dose: doseVal })}
                    onMouseLeave={() => setHoveredNode(null)}
                  />
                ) : (
                  <circle
                    cx={sx}
                    cy={sy}
                    r={radius}
                    fill={fill}
                    stroke={isCentre ? '#78350f' : '#042f2e'}
                    strokeWidth={1.2}
                    className="cursor-pointer hover:scale-125 transition-transform"
                    onMouseEnter={() => setHoveredNode({ id: idx, x, y, dose: doseVal })}
                    onMouseLeave={() => setHoveredNode(null)}
                  />
                )}
              </g>
            );
          })}

          {/* Axis labels */}
          <text x={svgWidth / 2} y={svgHeight - 12} textAnchor="middle" className="text-[11px] fill-slate-500 font-medium">
            X Spatial Coordinate (m)
          </text>
          <text
            x={-svgHeight / 2}
            y={16}
            transform="rotate(-90)"
            textAnchor="middle"
            className="text-[11px] fill-slate-500 font-medium"
          >
            Y Spatial Coordinate (m)
          </text>
        </svg>

        {/* Hover Tooltip */}
        {hoveredNode && (
          <div className="absolute top-4 right-4 bg-slate-900/90 text-white text-xs rounded-lg px-3 py-2 shadow-lg backdrop-blur-xs pointer-events-none">
            <div className="font-semibold text-slate-200">
              {hoveredNode.id === mesh.centreNodeIndex
                ? '⭐ Centre Evaluation Node'
                : mesh.isBoundary[hoveredNode.id]
                ? 'Boundary Node'
                : 'Interior Node'}
            </div>
            <div className="text-slate-300">
              (X: {hoveredNode.x.toFixed(4)}, Y: {hoveredNode.y.toFixed(4)})
            </div>
            {hoveredNode.dose !== undefined && (
              <div className="text-teal-300 font-mono mt-0.5">
                FEM Dose D: {hoveredNode.dose.toFixed(6)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
