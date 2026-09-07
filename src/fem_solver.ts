/**
 * Finite Element Method (FEM) 2D Numerical Solver in TypeScript
 * Solves: -k ∇²D = S
 * Weak Form: ∫_Ω k (∇D · ∇v) dΩ = ∫_Ω S v dΩ
 * Linear System: [K]{D} = {F}
 * 3-node Linear Triangular Finite Elements (CST)
 */

import { ModelParams, FEMMesh, FEMElement, FEMSolutionData } from './types';

/**
 * Solve linear system M * x = b via Gaussian elimination with partial pivoting
 */
function solveSystem(A: number[][], b: number[]): number[] {
  const n = b.length;
  const M: number[][] = new Array(n);
  for (let i = 0; i < n; i++) {
    M[i] = new Array(n + 1);
    for (let j = 0; j < n; j++) {
      M[i][j] = A[i][j];
    }
    M[i][n] = b[i];
  }

  // Forward elimination
  for (let i = 0; i < n; i++) {
    let maxRow = i;
    let maxVal = Math.abs(M[i][i]);
    for (let k = i + 1; k < n; k++) {
      const val = Math.abs(M[k][i]);
      if (val > maxVal) {
        maxVal = val;
        maxRow = k;
      }
    }

    if (maxVal < 1e-13) {
      throw new Error('FEM global stiffness matrix is singular or ill-conditioned.');
    }

    if (maxRow !== i) {
      const temp = M[i];
      M[i] = M[maxRow];
      M[maxRow] = temp;
    }

    const pivot = M[i][i];
    for (let k = i + 1; k < n; k++) {
      const factor = M[k][i] / pivot;
      for (let j = i; j <= n; j++) {
        M[k][j] -= factor * M[i][j];
      }
    }
  }

  // Back substitution
  const x = new Array(n).fill(0);
  for (let i = n - 1; i >= 0; i--) {
    let sum = 0;
    for (let j = i + 1; j < n; j++) {
      sum += M[i][j] * x[j];
    }
    x[i] = (M[i][n] - sum) / M[i][i];
  }

  return x;
}

/**
 * Generates structured 2D triangular finite element mesh over domain
 */
export function generateFEMMesh(params: ModelParams): FEMMesh {
  const Lx = params.xmax - params.xmin;
  const Ly = params.ymax - params.ymin;
  const Nx = Math.round(Lx / params.h) + 1;
  const Ny = Math.round(Ly / params.h) + 1;

  const dx = Lx / (Nx - 1);
  const dy = Ly / (Ny - 1);

  const nodes: [number, number][] = [];
  const isBoundary: boolean[] = [];

  for (let j = 0; j < Ny; j++) {
    const y = Number((params.ymin + j * dy).toFixed(6));
    for (let i = 0; i < Nx; i++) {
      const x = Number((params.xmin + i * dx).toFixed(6));
      nodes.push([x, y]);
      const boundaryFlag = i === 0 || i === Nx - 1 || j === 0 || j === Ny - 1;
      isBoundary.push(boundaryFlag);
    }
  }

  const totalNodes = nodes.length;
  const boundaryNodesCount = isBoundary.filter(Boolean).length;
  const interiorNodesCount = totalNodes - boundaryNodesCount;

  // Triangular elements (2 triangles per rectangle)
  const elements: FEMElement[] = [];
  let elemId = 0;

  for (let j = 0; j < Ny - 1; j++) {
    for (let i = 0; i < Nx - 1; i++) {
      const n00 = j * Nx + i;
      const n10 = j * Nx + (i + 1);
      const n01 = (j + 1) * Nx + i;
      const n11 = (j + 1) * Nx + (i + 1);

      // Triangle 1: (n00, n10, n11)
      const v1 = nodes[n00];
      const v2 = nodes[n10];
      const v3 = nodes[n11];
      const detJ1 = (v2[0] - v1[0]) * (v3[1] - v1[1]) - (v3[0] - v1[0]) * (v2[1] - v1[1]);
      const area1 = 0.5 * Math.abs(detJ1);
      const centroid1: [number, number] = [
        (v1[0] + v2[0] + v3[0]) / 3,
        (v1[1] + v2[1] + v3[1]) / 3
      ];

      elements.push({
        id: elemId++,
        nodes: [n00, n10, n11],
        vertices: [v1, v2, v3],
        area: area1,
        centroid: centroid1
      });

      // Triangle 2: (n00, n11, n01)
      const w1 = nodes[n00];
      const w2 = nodes[n11];
      const w3 = nodes[n01];
      const detJ2 = (w2[0] - w1[0]) * (w3[1] - w1[1]) - (w3[0] - w1[0]) * (w2[1] - w1[1]);
      const area2 = 0.5 * Math.abs(detJ2);
      const centroid2: [number, number] = [
        (w1[0] + w2[0] + w3[0]) / 3,
        (w1[1] + w2[1] + w3[1]) / 3
      ];

      elements.push({
        id: elemId++,
        nodes: [n00, n11, n01],
        vertices: [w1, w2, w3],
        area: area2,
        centroid: centroid2
      });
    }
  }

  // Find centre node
  const cxIdeal = (params.xmin + params.xmax) / 2;
  const cyIdeal = (params.ymin + params.ymax) / 2;
  let bestIdx = 0;
  let minDist = Infinity;

  for (let idx = 0; idx < totalNodes; idx++) {
    if (!isBoundary[idx]) {
      const [x, y] = nodes[idx];
      const dist = Math.hypot(x - cxIdeal, y - cyIdeal);
      if (dist < minDist) {
        minDist = dist;
        bestIdx = idx;
      }
    }
  }

  return {
    nodes,
    elements,
    totalNodes,
    totalElements: elements.length,
    isBoundary,
    interiorNodesCount,
    boundaryNodesCount,
    centreNodeIndex: bestIdx,
    centreCoords: nodes[bestIdx],
    Nx,
    Ny
  };
}

/**
 * Computes element stiffness matrix for linear triangle
 */
function computeElementStiffness(
  pts: [[number, number], [number, number], [number, number]],
  k: number
): { Ke: number[][]; area: number } {
  const [p1, p2, p3] = pts;
  const [x1, y1] = p1;
  const [x2, y2] = p2;
  const [x3, y3] = p3;

  const detJ = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1);
  const area = 0.5 * Math.abs(detJ);

  const b1 = y2 - y3;
  const c1 = x3 - x2;
  const b2 = y3 - y1;
  const c2 = x1 - x3;
  const b3 = y1 - y2;
  const c3 = x2 - x1;

  const bs = [b1, b2, b3];
  const cs = [c1, c2, c3];

  const Ke: number[][] = [
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0]
  ];

  const factor = k / (4 * area);
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      Ke[i][j] = factor * (bs[i] * bs[j] + cs[i] * cs[j]);
    }
  }

  return { Ke, area };
}

/**
 * Full FEM Solver workflow:
 * 1. Mesh generation
 * 2. Element stiffness & load assembly
 * 3. Dirichlet boundary conditions
 * 4. Linear solve [K]{D} = {F}
 * 5. Extraction of centre dose and statistics
 */
export function solveFEM(params: ModelParams): FEMSolutionData {
  const startTime = performance.now();
  const mesh = generateFEMMesh(params);
  const N = mesh.totalNodes;

  const K: number[][] = Array.from({ length: N }, () => new Array(N).fill(0));
  const F: number[] = new Array(N).fill(0);

  // Global assembly
  for (const elem of mesh.elements) {
    const { Ke, area } = computeElementStiffness(elem.vertices, params.k);
    const Fe = (params.S * area) / 3;
    const [n1, n2, n3] = elem.nodes;
    const eNodes = [n1, n2, n3];

    for (let i = 0; i < 3; i++) {
      F[eNodes[i]] += Fe;
      for (let j = 0; j < 3; j++) {
        K[eNodes[i]][eNodes[j]] += Ke[i][j];
      }
    }
  }

  // Dirichlet Boundary Conditions
  for (let i = 0; i < N; i++) {
    if (mesh.isBoundary[i]) {
      // Adjust interior loads
      for (let j = 0; j < N; j++) {
        if (j !== i && !mesh.isBoundary[j]) {
          F[j] -= K[j][i] * params.boundaryDose;
        }
      }
      // Zero out row and col
      for (let j = 0; j < N; j++) {
        K[i][j] = 0;
        K[j][i] = 0;
      }
      K[i][i] = 1;
      F[i] = params.boundaryDose;
    }
  }

  // Direct solve
  const nodalDoses = solveSystem(K, F);

  const endTime = performance.now();
  const executionTimeMs = Math.max(endTime - startTime, 0.01);

  // Reconstruct structured 2D dose grid D[j][i]
  const Nx = mesh.Nx;
  const Ny = mesh.Ny;
  const doseMatrix: number[][] = Array.from({ length: Ny }, () => new Array(Nx).fill(0));

  for (let j = 0; j < Ny; j++) {
    for (let i = 0; i < Nx; i++) {
      const idx = j * Nx + i;
      doseMatrix[j][i] = nodalDoses[idx];
    }
  }

  const centreDose = nodalDoses[mesh.centreNodeIndex];

  // Statistics
  const sorted = [...nodalDoses].sort((a, b) => a - b);
  const minDose = sorted[0];
  const maxDose = sorted[sorted.length - 1];
  const meanDose = sorted.reduce((a, b) => a + b, 0) / sorted.length;
  const medianDose =
    sorted.length % 2 === 1
      ? sorted[Math.floor(sorted.length / 2)]
      : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2;
  const variance =
    sorted.reduce((acc, v) => acc + Math.pow(v - meanDose, 2), 0) / sorted.length;
  const stdDose = Math.sqrt(variance);

  return {
    mesh,
    nodalDoses,
    doseMatrix,
    centreDose,
    maxDose,
    minDose,
    meanDose,
    medianDose,
    stdDose,
    matrixDim: mesh.interiorNodesCount,
    executionTimeMs
  };
}
