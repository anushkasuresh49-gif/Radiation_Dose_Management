/**
 * TypeScript Interfaces for Radiation Dose FDM Simulation Dashboard
 */

export interface ModelParams {
  xmin: number;
  xmax: number;
  ymin: number;
  ymax: number;
  k: number; // diffusion coefficient
  S: number; // source intensity
  h: number; // grid spacing
  boundaryDose: number; // Dirichlet boundary dose
}

export interface GridData {
  Nx: number;
  Ny: number;
  totalNodes: number;
  interiorNodesCount: number;
  boundaryNodesCount: number;
  xCoords: number[];
  yCoords: number[];
  centreIndex: [number, number]; // [i, j]
  nodeTypes: ('boundary' | 'interior' | 'centre')[][];
}

export interface FDMSolutionData {
  grid: GridData;
  doseMatrix: number[][]; // [j][i]
  centreDose: number;
  maxDose: number;
  minDose: number;
  meanDose: number;
  medianDose: number;
  stdDose: number;
  matrixDim: number;
  executionTimeMs: number;
  equationsDerived: string;
}

export interface ValidationData {
  fdmCentreDose: number;
  referenceDose: number;
  absoluteError: number;
  relativeErrorPct: number;
  referenceLabel: string;
}

export interface ConvergenceItem {
  h: number;
  gridPoints: number;
  interiorNodes: number;
  centreDose: number;
  absoluteError: number;
  relativeErrorPct: number;
  executionTimeMs: number;
}

export interface SensitivityData {
  kValues: number[];
  kDoses: number[];
  sValues: number[];
  sDoses: number[];
  hValues: number[];
  hDoses: number[];
  interpretation: string;
}

export interface TumourParams {
  cx: number;
  cy: number;
  radius: number;
}

export interface TumourMetrics {
  avgTumourDose: number;
  maxTumourDose: number;
  avgSurroundingDose: number;
  maxSurroundingDose: number;
  tumourToSurroundingRatio: number;
  tumourNodesCount: number;
  surroundingNodesCount: number;
}
