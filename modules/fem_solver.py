"""
Module: fem_solver.py
Finite Element Method (FEM) 2D Numerical Solver for Radiation Dose Poisson PDE
Governing Equation: -k ∇²D = -k (∂²D/∂x² + ∂²D/∂y²) = S

Weak Form Formulation:
  ∫_Ω k (∇D · ∇v) dΩ = ∫_Ω S v dΩ
Matrix System:
  [K]{D} = {F}
Where:
  K = Global stiffness matrix assembled from element stiffness matrices K^e
  D = Nodal radiation dose vector
  F = Global load/source vector assembled from element load vectors F^e
  k = Diffusion coefficient
  S = Radiation source intensity

Element Formulation:
  3-node linear triangular elements (CST - Constant Strain Triangle)
  K^e_ij = (k / 4 A_e) * (b_i b_j + c_i c_j)
  F^e_i = (S * A_e) / 3
"""

from dataclasses import dataclass
from typing import Tuple, List, Dict, Any, Optional
import time
import math

from .model import ModelParameters, ComputationalGrid, validate_parameters

try:
    import numpy as np
    import scipy.sparse as sp
    from scipy.sparse.linalg import spsolve
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class FEMElement:
    """Represents a single 3-node triangular finite element."""
    element_id: int
    node_indices: Tuple[int, int, int]
    vertices: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]
    area: float
    centroid: Tuple[float, float]


@dataclass
class FEMMesh:
    """Structured triangular finite element mesh representation."""
    params: ModelParameters
    nodes: List[Tuple[float, float]]       # (x, y) coordinates for all nodes
    elements: List[FEMElement]             # List of triangular elements
    total_nodes: int
    total_elements: int
    is_boundary: List[bool]
    interior_nodes_count: int
    boundary_nodes_count: int
    centre_node_index: int
    centre_coordinates: Tuple[float, float]
    Nx: int
    Ny: int


@dataclass
class FEMSolution:
    """Encapsulates the complete numerical solution from the FEM solver."""
    mesh: FEMMesh
    nodal_doses: List[float]               # Dose values at each node index
    dose_matrix: List[List[float]]         # Structured 2D grid representation D[j][i]
    centre_dose: float
    max_dose: float
    min_dose: float
    mean_dose: float
    median_dose: float
    std_dose: float
    matrix_dim: int                        # Number of system degrees of freedom
    execution_time_sec: float
    K_matrix_sample: Optional[List[List[float]]]
    F_vector_sample: Optional[List[float]]


def _solve_dense_system_pure_python(A: List[List[float]], b: List[float]) -> List[float]:
    """
    Gaussian elimination with partial pivoting for fallback when numpy/scipy is unavailable.
    """
    n = len(b)
    M = [A[i][:] + [b[i]] for i in range(n)]

    for i in range(n):
        max_row = i
        max_val = abs(M[i][i])
        for k in range(i + 1, n):
            if abs(M[k][i]) > max_val:
                max_val = abs(M[k][i])
                max_row = k

        if abs(max_val) < 1e-14:
            raise ValueError("FEM global stiffness matrix is singular or ill-conditioned.")

        if max_row != i:
            M[i], M[max_row] = M[max_row], M[i]

        pivot = M[i][i]
        for k in range(i + 1, n):
            factor = M[k][i] / pivot
            for j in range(i, n + 1):
                M[k][j] -= factor * M[i][j]

    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = sum(M[i][j] * x[j] for j in range(i + 1, n))
        x[i] = (M[i][n] - s) / M[i][i]

    return x


def generate_triangular_mesh(params: ModelParameters) -> FEMMesh:
    """
    Step 1 & 2 & 3: Mesh generation, Node coordinates, and Element connectivity.
    Constructs a structured 2D triangular finite element mesh over [xmin, xmax] x [ymin, ymax].
    Each rectangular cell is subdivided into 2 linear triangular elements.
    """
    valid, err = validate_parameters(params)
    if not valid:
        raise ValueError(err)

    Lx = params.Lx
    Ly = params.Ly
    Nx = int(round(Lx / params.h)) + 1
    Ny = int(round(Ly / params.h)) + 1

    dx = Lx / (Nx - 1)
    dy = Ly / (Ny - 1)

    nodes: List[Tuple[float, float]] = []
    is_boundary: List[bool] = []

    # Generate nodes with row-major indexing: index = j * Nx + i
    for j in range(Ny):
        y = round(params.ymin + j * dy, 6)
        for i in range(Nx):
            x = round(params.xmin + i * dx, 6)
            nodes.append((x, y))
            boundary_flag = (i == 0 or i == Nx - 1 or j == 0 or j == Ny - 1)
            is_boundary.append(boundary_flag)

    total_nodes = len(nodes)
    boundary_nodes_count = sum(1 for b in is_boundary if b)
    interior_nodes_count = total_nodes - boundary_nodes_count

    # Generate triangular elements (2 triangles per Cartesian cell)
    elements: List[FEMElement] = []
    elem_id = 0

    for j in range(Ny - 1):
        for i in range(Nx - 1):
            n00 = j * Nx + i
            n10 = j * Nx + (i + 1)
            n01 = (j + 1) * Nx + i
            n11 = (j + 1) * Nx + (i + 1)

            # Triangle 1: (n00, n10, n11)
            v1_t1 = nodes[n00]
            v2_t1 = nodes[n10]
            v3_t1 = nodes[n11]
            detJ1 = (v2_t1[0] - v1_t1[0]) * (v3_t1[1] - v1_t1[1]) - (v3_t1[0] - v1_t1[0]) * (v2_t1[1] - v1_t1[1])
            area1 = 0.5 * abs(detJ1)
            c1 = ((v1_t1[0] + v2_t1[0] + v3_t1[0]) / 3.0, (v1_t1[1] + v2_t1[1] + v3_t1[1]) / 3.0)

            elements.append(FEMElement(
                element_id=elem_id,
                node_indices=(n00, n10, n11),
                vertices=(v1_t1, v2_t1, v3_t1),
                area=area1,
                centroid=c1
            ))
            elem_id += 1

            # Triangle 2: (n00, n11, n01)
            v1_t2 = nodes[n00]
            v2_t2 = nodes[n11]
            v3_t2 = nodes[n01]
            detJ2 = (v2_t2[0] - v1_t2[0]) * (v3_t2[1] - v1_t2[1]) - (v3_t2[0] - v1_t2[0]) * (v2_t2[1] - v1_t2[1])
            area2 = 0.5 * abs(detJ2)
            c2 = ((v1_t2[0] + v2_t2[0] + v3_t2[0]) / 3.0, (v1_t2[1] + v2_t2[1] + v3_t2[1]) / 3.0)

            elements.append(FEMElement(
                element_id=elem_id,
                node_indices=(n00, n11, n01),
                vertices=(v1_t2, v2_t2, v3_t2),
                area=area2,
                centroid=c2
            ))
            elem_id += 1

    # Find centre node (closest to geometric domain centre)
    cx_ideal = (params.xmin + params.xmax) / 2.0
    cy_ideal = (params.ymin + params.ymax) / 2.0
    best_idx = 0
    min_dist = float('inf')

    for idx, (x, y) in enumerate(nodes):
        if not is_boundary[idx]:
            d = math.hypot(x - cx_ideal, y - cy_ideal)
            if d < min_dist:
                min_dist = d
                best_idx = idx

    centre_node_index = best_idx
    centre_coords = nodes[best_idx]

    return FEMMesh(
        params=params,
        nodes=nodes,
        elements=elements,
        total_nodes=total_nodes,
        total_elements=len(elements),
        is_boundary=is_boundary,
        interior_nodes_count=interior_nodes_count,
        boundary_nodes_count=boundary_nodes_count,
        centre_node_index=centre_node_index,
        centre_coordinates=centre_coords,
        Nx=Nx,
        Ny=Ny
    )


def compute_element_stiffness(pts: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]], k: float) -> Tuple[List[List[float]], float]:
    """
    Step 4 & 5: Element stiffness matrix for linear triangular element.
    Shape functions: N_i(x,y) = (a_i + b_i*x + c_i*y) / (2 * A_e)
    b_1 = y_2 - y_3,  c_1 = x_3 - x_2
    b_2 = y_3 - y_1,  c_2 = x_1 - x_3
    b_3 = y_1 - y_2,  c_3 = x_2 - x_1
    K^e_ij = ∫_Te k (∇N_i · ∇N_j) dΩ = (k / (4 A_e)) * (b_i b_j + c_i c_j)
    """
    (x1, y1), (x2, y2), (x3, y3) = pts
    detJ = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    Ae = 0.5 * abs(detJ)
    if Ae < 1e-14:
        raise ValueError("Degenerate triangular element with zero area.")

    b1 = y2 - y3
    c1 = x3 - x2
    b2 = y3 - y1
    c2 = x1 - x3
    b3 = y1 - y2
    c3 = x2 - x1

    bs = [b1, b2, b3]
    cs = [c1, c2, c3]

    Ke = [[0.0] * 3 for _ in range(3)]
    factor = k / (4.0 * Ae)
    for i in range(3):
        for j in range(3):
            Ke[i][j] = factor * (bs[i] * bs[j] + cs[i] * cs[j])

    return Ke, Ae


def compute_element_load(Ae: float, S: float) -> List[float]:
    """
    Step 6: Element load/source vector for constant source intensity S.
    F^e_i = ∫_Te S N_i dΩ = S * A_e / 3
    """
    val = (S * Ae) / 3.0
    return [val, val, val]


def assemble_global_fem_system(mesh: FEMMesh) -> Tuple[Any, Any]:
    """
    Step 7, 8, & 9: Global stiffness matrix assembly, load vector assembly,
    and Dirichlet boundary condition application.
    [K]{D} = {F}
    """
    params = mesh.params
    k = params.k
    S = params.S
    D_b = params.boundary_dose
    N = mesh.total_nodes

    if HAS_NUMPY:
        K_mat = sp.lil_matrix((N, N), dtype=float)
        F_vec = np.zeros(N, dtype=float)

        for elem in mesh.elements:
            pts = elem.vertices
            Ke, Ae = compute_element_stiffness(pts, k)
            Fe = compute_element_load(Ae, S)
            nodes_e = elem.node_indices

            for i in range(3):
                gi = nodes_e[i]
                F_vec[gi] += Fe[i]
                for j in range(3):
                    gj = nodes_e[j]
                    K_mat[gi, gj] += Ke[i][j]

        # Apply Dirichlet Boundary Conditions: D(boundary) = D_b
        # Row-elimination method: for boundary node i, set K[i, :] = 0, K[i, i] = 1, F[i] = D_b
        # and adjust RHS F[j] -= K[j, i] * D_b for non-boundary nodes j.
        for i in range(N):
            if mesh.is_boundary[i]:
                # Adjust RHS of interior neighbors
                cols, vals = K_mat.getrow(i).indices, K_mat.getrow(i).data
                # In lil_matrix, iterate non-zero columns
                row_cols = list(K_mat.rows[i])
                row_vals = list(K_mat.data[i])
                for col, val in zip(row_cols, row_vals):
                    if col != i and not mesh.is_boundary[col]:
                        F_vec[col] -= val * D_b

                # Clear row and column
                K_mat.rows[i] = [i]
                K_mat.data[i] = [1.0]
                F_vec[i] = D_b

        # Also clear column for boundary nodes to keep symmetry
        K_csr = K_mat.tocsr()
        return K_csr, F_vec

    else:
        # Pure Python list-of-lists assembly
        K = [[0.0] * N for _ in range(N)]
        F = [0.0] * N

        for elem in mesh.elements:
            pts = elem.vertices
            Ke, Ae = compute_element_stiffness(pts, k)
            Fe = compute_element_load(Ae, S)
            nodes_e = elem.node_indices

            for i in range(3):
                gi = nodes_e[i]
                F[gi] += Fe[i]
                for j in range(3):
                    gj = nodes_e[j]
                    K[gi][gj] += Ke[i][j]

        # Apply Dirichlet boundary conditions
        for i in range(N):
            if mesh.is_boundary[i]:
                for j in range(N):
                    if j != i and not mesh.is_boundary[j]:
                        F[j] -= K[j][i] * D_b
                for j in range(N):
                    K[i][j] = 0.0
                    K[j][i] = 0.0
                K[i][i] = 1.0
                F[i] = D_b

        return K, F


def solve_fem(params: ModelParameters) -> FEMSolution:
    """
    Executes the complete 12-step FEM solver workflow:
    1. Triangular mesh generation
    2. Node coordinates determination
    3. Element connectivity definition
    4. Triangular finite elements
    5. Element stiffness matrix computation [Ke]
    6. Element source/load vector computation {Fe}
    7. Global stiffness matrix assembly [K]
    8. Global load vector assembly {F}
    9. Application of Dirichlet boundary conditions
    10. Solution of linear system [K]{D} = {F}
    11. Reconstruction of 2D FEM dose field
    12. Extraction of centre-point dose and statistics
    """
    t_start = time.perf_counter()

    mesh = generate_triangular_mesh(params)
    K, F = assemble_global_fem_system(mesh)
    N = mesh.total_nodes

    if HAS_NUMPY and sp.issparse(K):
        nodal_solution = spsolve(K, F)
        if isinstance(nodal_solution, np.ndarray):
            d_nodal = nodal_solution.tolist()
        else:
            d_nodal = list(nodal_solution)
    elif HAS_NUMPY and isinstance(K, np.ndarray):
        nodal_solution = np.linalg.solve(K, F)
        d_nodal = nodal_solution.tolist()
    else:
        d_nodal = _solve_dense_system_pure_python(K, F)

    t_end = time.perf_counter()
    execution_time = max(t_end - t_start, 1e-6)

    # Step 11: Reconstruct 2D dose matrix for grid-based visualization D[j][i]
    Nx = mesh.Nx
    Ny = mesh.Ny
    dose_matrix = [[0.0 for _ in range(Nx)] for _ in range(Ny)]
    for j in range(Ny):
        for i in range(Nx):
            idx = j * Nx + i
            dose_matrix[j][i] = float(d_nodal[idx])

    # Step 12: Centre-point dose extraction
    centre_dose = float(d_nodal[mesh.centre_node_index])

    # Summary statistics
    sorted_doses = sorted(d_nodal)
    min_dose = sorted_doses[0]
    max_dose = sorted_doses[-1]
    mean_dose = sum(sorted_doses) / len(sorted_doses)
    n = len(sorted_doses)
    median_dose = sorted_doses[n // 2] if n % 2 == 1 else (sorted_doses[n // 2 - 1] + sorted_doses[n // 2]) / 2.0
    var = sum((v - mean_dose) ** 2 for v in sorted_doses) / n
    std_dose = math.sqrt(var)

    # Sample submatrix for inspection
    sample_dim = min(N, 5)
    if HAS_NUMPY and sp.issparse(K):
        K_sub = K[:sample_dim, :sample_dim].toarray().tolist()
        F_sub = F[:sample_dim].tolist()
    elif isinstance(K, list):
        K_sub = [row[:sample_dim] for row in K[:sample_dim]]
        F_sub = F[:sample_dim]
    else:
        K_sub = None
        F_sub = None

    return FEMSolution(
        mesh=mesh,
        nodal_doses=d_nodal,
        dose_matrix=dose_matrix,
        centre_dose=centre_dose,
        max_dose=max_dose,
        min_dose=min_dose,
        mean_dose=mean_dose,
        median_dose=median_dose,
        std_dose=std_dose,
        matrix_dim=mesh.interior_nodes_count,
        execution_time_sec=execution_time,
        K_matrix_sample=K_sub,
        F_vector_sample=F_sub
    )
