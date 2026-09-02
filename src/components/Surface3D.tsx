import React, { useRef, useEffect, useState } from 'react';
import { FDMSolutionData } from '../types';
import { Rotate3d, ZoomIn, ZoomOut, RefreshCw } from 'lucide-react';

interface Surface3DProps {
  sol: FDMSolutionData;
}

export const Surface3D: React.FC<Surface3DProps> = ({ sol }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [rotX, setRotX] = useState<number>(35); // degrees
  const [rotZ, setRotZ] = useState<number>(45); // degrees
  const [zoom, setZoom] = useState<number>(1.0);
  const isDragging = useRef<boolean>(false);
  const lastMousePos = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const { grid, doseMatrix, minDose, maxDose } = sol;
  const { Nx, Ny, xCoords, yCoords } = grid;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    // Dark background for crisp 3D visualization
    ctx.fillStyle = '#07090e';
    ctx.fillRect(0, 0, width, height);

    const radX = (rotX * Math.PI) / 180;
    const radZ = (rotZ * Math.PI) / 180;

    const cosX = Math.cos(radX);
    const sinX = Math.sin(radX);
    const cosZ = Math.cos(radZ);
    const sinZ = Math.sin(radZ);

    const cx = width / 2;
    const cy = height / 2 + 30;
    const scale = 140 * zoom;

    const doseRange = maxDose - minDose || 1;

    // Transform 3D point (x, y, z) into 2D screen coordinates
    // Normalize coordinates to [-1, 1]
    const xMin = xCoords[0];
    const xMax = xCoords[Nx - 1];
    const yMin = yCoords[0];
    const yMax = yCoords[Ny - 1];

    const project = (xVal: number, yVal: number, zVal: number) => {
      const nx = ((xVal - xMin) / (xMax - xMin || 1) - 0.5) * 2;
      const ny = ((yVal - yMin) / (yMax - yMin || 1) - 0.5) * 2;
      const nz = ((zVal - minDose) / doseRange) * 1.5; // height

      // Rotate around Z
      const rx = nx * cosZ - ny * sinZ;
      const ry = nx * sinZ + ny * cosZ;

      // Rotate around X
      const py = ry * cosX - nz * sinX;
      const pz = ry * sinX + nz * cosX;

      const screenX = cx + rx * scale;
      const screenY = cy - (py + pz * 0.8) * scale * 0.8;

      return { x: screenX, y: screenY, depth: pz };
    };

    // Draw base boundary grid
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;

    const corners = [
      project(xMin, yMin, minDose),
      project(xMax, yMin, minDose),
      project(xMax, yMax, minDose),
      project(xMin, yMax, minDose)
    ];

    ctx.beginPath();
    ctx.moveTo(corners[0].x, corners[0].y);
    for (let c = 1; c < 4; c++) ctx.lineTo(corners[c].x, corners[c].y);
    ctx.closePath();
    ctx.stroke();

    // Sort polygons back-to-front by average depth
    type Quad = {
      p0: { x: number; y: number; depth: number };
      p1: { x: number; y: number; depth: number };
      p2: { x: number; y: number; depth: number };
      p3: { x: number; y: number; depth: number };
      depth: number;
      avgDose: number;
    };

    const quads: Quad[] = [];

    for (let j = 0; j < Ny - 1; j++) {
      for (let i = 0; i < Nx - 1; i++) {
        const p0 = project(xCoords[i], yCoords[j], doseMatrix[j][i]);
        const p1 = project(xCoords[i + 1], yCoords[j], doseMatrix[j][i + 1]);
        const p2 = project(xCoords[i + 1], yCoords[j + 1], doseMatrix[j + 1][i + 1]);
        const p3 = project(xCoords[i], yCoords[j + 1], doseMatrix[j + 1][i]);

        const depth = (p0.depth + p1.depth + p2.depth + p3.depth) / 4;
        const avgDose =
          (doseMatrix[j][i] +
            doseMatrix[j][i + 1] +
            doseMatrix[j + 1][i + 1] +
            doseMatrix[j + 1][i]) /
          4;

        quads.push({ p0, p1, p2, p3, depth, avgDose });
      }
    }

    quads.sort((a, b) => a.depth - b.depth);

    // Draw shaded surface patches
    for (const q of quads) {
      const t = (q.avgDose - minDose) / doseRange;
      // Gradient from dark indigo/teal to vibrant amber
      const r = Math.round(30 + t * 225);
      const g = Math.round(90 + t * 110);
      const b = Math.round(180 - t * 130);

      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.88)`;
      ctx.strokeStyle = `rgba(${r + 25}, ${g + 25}, ${b + 25}, 0.95)`;
      ctx.lineWidth = 0.8;

      ctx.beginPath();
      ctx.moveTo(q.p0.x, q.p0.y);
      ctx.lineTo(q.p1.x, q.p1.y);
      ctx.lineTo(q.p2.x, q.p2.y);
      ctx.lineTo(q.p3.x, q.p3.y);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // Draw peak pointer
    const [ci, cj] = grid.centreIndex;
    const peakPt = project(xCoords[ci], yCoords[cj], sol.centreDose);
    ctx.fillStyle = '#ef4444';
    ctx.beginPath();
    ctx.arc(peakPt.x, peakPt.y, 4.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#f8fafc';
    ctx.font = '11px monospace';
    ctx.fillText(`Peak: ${sol.centreDose.toFixed(4)}`, peakPt.x + 8, peakPt.y - 4);
  }, [sol, rotX, rotZ, zoom, Nx, Ny, doseMatrix, minDose, maxDose]);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDragging.current = true;
    lastMousePos.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging.current) return;
    const dx = e.clientX - lastMousePos.current.x;
    const dy = e.clientY - lastMousePos.current.y;
    lastMousePos.current = { x: e.clientX, y: e.clientY };

    setRotZ((prev) => (prev + dx * 0.5) % 360);
    setRotX((prev) => Math.max(10, Math.min(80, prev - dy * 0.5)));
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm text-slate-200">
      <div className="mb-2 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white">3D Radiation Dose Surface Topology</h3>
          <p className="text-xs text-slate-400">Interactive elevation model showing radial diffusion decay</p>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setZoom((z) => Math.min(1.8, z + 0.1))}
            className="rounded-lg border border-slate-800 bg-slate-800/60 p-1.5 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}
            className="rounded-lg border border-slate-800 bg-slate-800/60 p-1.5 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <button
            onClick={() => {
              setRotX(35);
              setRotZ(45);
              setZoom(1.0);
            }}
            className="rounded-lg border border-slate-800 bg-slate-800/60 p-1.5 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
            title="Reset View"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="relative flex justify-center">
        <canvas
          ref={canvasRef}
          width={500}
          height={380}
          className="cursor-grab active:cursor-grabbing rounded-lg border border-slate-800/80 bg-[#07090e]"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        />
        <div className="absolute bottom-2 right-2 rounded-lg bg-slate-950/90 border border-slate-800 px-2.5 py-1 text-[11px] text-slate-300 pointer-events-none flex items-center gap-1.5 shadow-md">
          <Rotate3d className="h-3.5 w-3.5 text-indigo-400" /> Click and drag to rotate surface
        </div>
      </div>

      <div className="mt-2 text-center text-xs text-slate-400 font-mono">
        Rot X: {rotX.toFixed(0)}° | Rot Z: {rotZ.toFixed(0)}° | Elevation proportional to absorbed dose
      </div>
    </div>
  );
};
