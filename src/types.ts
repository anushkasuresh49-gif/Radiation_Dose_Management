/**
 * TypeScript Interfaces for Radiation Dose FDM & FEM Simulation Dashboard
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

export interface FEMElement {
  id: number;
  nodes: [number, number, number]; // indices into mesh nodes
  vertices: [[number, number], [number, number], [number, number]];
  area: number;
  centroid: [number, number];
}

export interface FEMMesh {
  nodes: [number, number][]; // (x, y) coordinates
  elements: FEMElement[];
  totalNodes: number;
  totalElements: number;
  isBoundary: boolean[];
  interiorNodesCount: number;
  boundaryNodesCount: number;
  centreNodeIndex: number;
  centreCoords: [number, number];
  Nx: number;
  Ny: number;
}

export interface FEMSolutionData {
  mesh: FEMMesh;
  nodalDoses: number[];
  doseMatrix: number[][]; // reconstructed structured grid representation
  centreDose: number;
  maxDose: number;
  minDose: number;
  meanDose: number;
  medianDose: number;
  stdDose: number;
  matrixDim: number;
  executionTimeMs: number;
  stiffnessSample?: number[][];
}

export interface ValidationData {
  fdmCentreDose: number;
  femCentreDose: number;
  pptBenchmark: number;
  continuousAnalyticalDose: number;
  fdmVsPptAbsError: number;
  fdmVsPptRelErrorPct: number;
  femVsPptAbsError: number;
  femVsPptRelErrorPct: number;
  fdmVsAnaAbsError: number;
  fdmVsAnaRelErrorPct: number;
  femVsAnaAbsError: number;
  femVsAnaRelErrorPct: number;
  // Legacy / convenience fields
  referenceDose: number;
  absoluteError: number;
  relativeErrorPct: number;
  referenceLabel: string;
}

export interface ConvergenceItem {
  h: number;
  gridPoints: number;
  interiorNodes: number;
  femElements: number;
  fdmCentreDose: number;
  femCentreDose: number;
  referenceDose: number;
  fdmAbsError: number;
  femAbsError: number;
  fdmRelErrorPct: number;
  femRelErrorPct: number;
  fdmTimeMs: number;
  femTimeMs: number;
  // legacy aliases
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
