"""
Module: fdm_solver.py
Finite Difference Method (FDM) Numerical Solver for Radiation Dose Poisson PDE
Equation: -k (∂²D/∂x² + ∂²D/∂y²) = S
Discretization: 4 D(i,j) - D(i+1,j) - D(i-1,j) - D(i,j+1) - D(i,j-1) = (S * h²) / k
"""

from dataclasses import dataclass
from typing import Tuple, List, Dict, Any, Optional
import time
import math

from .model import ModelParameters, ComputationalGrid, create_grid, validate_parameters

try:
    import numpy as np
    import scipy.sparse as sp
    from scipy.sparse.linalg import spsolve
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class FDMSolution:
    """Encapsulates the complete numerical solution from FDM."""
    grid: ComputationalGrid
    dose_matrix: List[List[float]]  # 2D grid of dose values D[j][i]
    centre_dose: float
    max_dose: float
    min_dose: float
    mean_dose: float
    median_dose: float
    std_dose: float
    matrix_dim: int
    execution_time_sec: float
    A_matrix_sample: Optional[List[List[float]]]
    b_vector_sample: Optional[List[float]]
    interior_mapping: Dict[Tuple[int, int], int]


def _solve_dense_system_pure_python(A: List[List[float]], b: List[float]) -> List[float]:
    """
    Gaussian elimination with partial pivoting for fallback execution when numpy/scipy is unavailable.
    """
    n = len(b)
    # Augmented matrix
    M = [A[i][:] + [b[i]] for i in range(n)]

    for i in range(n):
        # Pivot
        max_row = i
        max_val = abs(M[i][i])
        for k in range(i + 1, n):
            if abs(M[k][i]) > max_val:
                max_val = abs(M[k][i])
                max_row = k

        if abs(max_val) < 1e-14:
            raise ValueError("Numerical system matrix is singular or ill-conditioned.")

        if max_row != i:
            M[i], M[max_row] = M[max_row], M[i]

        pivot = M[i][i]
        for k in range(i + 1, n):
            factor = M[k][i] / pivot
            for j in range(i, n + 1):
                M[k][j] -= factor * M[i][j]

    # Back-substitution
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = sum(M[i][j] * x[j] for j in range(i + 1, n))
        x[i] = (M[i][n] - s) / M[i][i]

    return x


def build_fdm_system(grid: ComputationalGrid) -> Tuple[Any, Any, Dict[Tuple[int, int], int]]:
    """
    Constructs the linear system A * D = b for the interior grid nodes.
    
    Governing discrete formula:
    4*D(i,j) - D(i+1,j) - D(i-1,j) - D(i,j+1) - D(i,j-1) = (S * h²) / k
    """
    params = grid.params
    Nx = grid.Nx
    Ny = grid.Ny
    h = params.h
    k = params.k
    S = params.S
    D_b = params.boundary_dose

    # Map each interior node (i, j) to an equation index 0 .. N_interior-1
    interior_nodes = []
    for j in range(1, Ny - 1):
        for i in range(1, Nx - 1):
            interior_nodes.append((i, j))

    N_interior = len(interior_nodes)
    node_to_idx = {node: idx for idx, node in enumerate(interior_nodes)}

    rhs_source = (S * (h ** 2)) / k

    if HAS_NUMPY:
        # Build using SciPy sparse lil_matrix or dok_matrix
        A_mat = sp.lil_matrix((N_interior, N_interior), dtype=float)
        b_vec = np.zeros(N_interior, dtype=float)

        for (i, j), row in node_to_idx.items():
            A_mat[row, row] = 4.0
            b_vec[row] = rhs_source

            # 4 neighbors: East, West, North, South
            neighbors = [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
            for ni, nj in neighbors:
                if 1 <= ni <= Nx - 2 and 1 <= nj <= Ny - 2:
                    col = node_to_idx[(ni, nj)]
                    A_mat[row, col] = -1.0
                else:
                    # Neighbor is on Dirichlet boundary
                    b_vec[row] += D_b

        return A_mat.tocsr(), b_vec, node_to_idx

    else:
        # Pure Python list-of-lists fallback
        A_list = [[0.0] * N_interior for _ in range(N_interior)]
        b_list = [rhs_source] * N_interior

        for (i, j), row in node_to_idx.items():
            A_list[row][row] = 4.0

            neighbors = [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
            for ni, nj in neighbors:
                if 1 <= ni <= Nx - 2 and 1 <= nj <= Ny - 2:
                    col = node_to_idx[(ni, nj)]
                    A_list[row][col] = -1.0
                else:
                    b_list[row] += D_b

        return A_list, b_list, node_to_idx


def solve_fdm(grid: ComputationalGrid) -> FDMSolution:
    """
    Executes the full 11-step FDM solver workflow:
    1. Grid input
    2. Boundary node recognition
    3. Interior node numbering
    4. Matrix formulation A
    5. RHS vector formulation b
    6. Boundary condition enforcement
    7. Solution of A D = b
    8. Full 2D reconstruction
    9. Centre-point dose extraction
    10. Statistical distribution calculation
    """
    t_start = time.perf_counter()

    A, b, node_to_idx = build_fdm_system(grid)
    N_interior = grid.interior_nodes_count

    if HAS_NUMPY and sp.issparse(A):
        # Solve with SciPy sparse linear solver
        sol_vec = spsolve(A, b)
        if isinstance(sol_vec, np.ndarray):
            d_solution = sol_vec.tolist()
        else:
            d_solution = list(sol_vec)
    elif HAS_NUMPY and isinstance(A, np.ndarray):
        sol_vec = np.linalg.solve(A, b)
        d_solution = sol_vec.tolist()
    else:
        d_solution = _solve_dense_system_pure_python(A, b)

    t_end = time.perf_counter()
    execution_time = max(t_end - t_start, 1e-6)

    # Step 9: Reconstruct complete 2D dose matrix
    dose_matrix = reconstruct_dose_matrix(grid, d_solution, node_to_idx)

    # Step 10: Extract centre-point dose
    ci, cj = grid.centre_index
    centre_dose = dose_matrix[cj][ci]

    # Step 11: Calculate dose statistics
    stats = calculate_dose_statistics(dose_matrix)

    # Sample submatrix for display
    sample_dim = min(N_interior, 5)
    if HAS_NUMPY and sp.issparse(A):
        A_sub = A[:sample_dim, :sample_dim].toarray().tolist()
        b_sub = b[:sample_dim].tolist()
    elif isinstance(A, list):
        A_sub = [row[:sample_dim] for row in A[:sample_dim]]
        b_sub = b[:sample_dim]
    else:
        A_sub = None
        b_sub = None

    return FDMSolution(
        grid=grid,
        dose_matrix=dose_matrix,
        centre_dose=centre_dose,
        max_dose=stats["max"],
        min_dose=stats["min"],
        mean_dose=stats["mean"],
        median_dose=stats["median"],
        std_dose=stats["std"],
        matrix_dim=N_interior,
        execution_time_sec=execution_time,
        A_matrix_sample=A_sub,
        b_vector_sample=b_sub,
        interior_mapping=node_to_idx
    )


def reconstruct_dose_matrix(
    grid: ComputationalGrid,
    interior_solution: List[float],
    node_to_idx: Dict[Tuple[int, int], int]
) -> List[List[float]]:
    """
    Rebuild the full Ny x Nx 2D array including boundary and interior values.
    """
    Nx = grid.Nx
    Ny = grid.Ny
    boundary_dose = grid.params.boundary_dose

    dose_matrix = [[boundary_dose for _ in range(Nx)] for _ in range(Ny)]

    for (i, j), idx in node_to_idx.items():
        dose_matrix[j][i] = float(interior_solution[idx])

    return dose_matrix


def calculate_dose_statistics(dose_matrix: List[List[float]]) -> Dict[str, float]:
    """
    Calculate summary statistics across all grid nodes.
    """
    all_values: List[float] = []
    for row in dose_matrix:
        all_values.extend(row)

    if not all_values:
        return {"max": 0.0, "min": 0.0, "mean": 0.0, "median": 0.0, "std": 0.0}

    all_values.sort()
    n = len(all_values)
    mean_val = sum(all_values) / n
    min_val = all_values[0]
    max_val = all_values[-1]

    if n % 2 == 1:
        median_val = all_values[n // 2]
    else:
        median_val = (all_values[n // 2 - 1] + all_values[n // 2]) / 2.0

    variance = sum((v - mean_val) ** 2 for v in all_values) / n
    std_val = math.sqrt(variance)

    return {
        "max": max_val,
        "min": min_val,
        "mean": mean_val,
        "median": median_val,
        "std": std_val
    }


def extract_centre_dose(dose_matrix: List[List[float]], centre_index: Tuple[int, int]) -> float:
    """Retrieve the computed dose value at the domain centre index."""
    ci, cj = centre_index
    return dose_matrix[cj][ci]


def generate_step_by_step_latex(params: ModelParameters, centre_dose: float) -> str:
    """
    Generates dynamic step-by-step LaTeX derivation for the single interior node case (e.g. h=0.5),
    or equivalent general system formulation.
    """
    k = params.k
    S = params.S
    h = params.h
    h2 = round(h * h, 6)
    b_val = params.boundary_dose

    if abs(h - 0.5) < 1e-4 and abs(params.Lx - 1.0) < 1e-4 and abs(params.Ly - 1.0) < 1e-4:
        # Default capstone demonstration case
        return rf"""
\begin{aligned}
\text{{Given parameters:}} \quad k &= {k}, \quad S = {S}, \quad h = {h}, \quad h^2 = {h2}, \quad D_{{\text{{boundary}}}} = {b_val} \\[6pt]
\text{{Governing PDE:}} \quad &-k \left( \frac{{\partial^2 D}}{{\partial x^2}} + \frac{{\partial^2 D}}{{\partial y^2}} \right) = S \\[6pt]
\text{{Central FDM Discretization at centre node }}(1, 1): \quad &-\left[ \frac{{D_{{2,1}} - 2D_{{1,1}} + D_{{0,1}}}}{{h^2}} + \frac{{D_{{1,2}} - 2D_{{1,1}} + D_{{1,0}}}}{{h^2}} \right] = \frac{{S}}{{k}} \\[6pt]
\text{{Substituting boundary values }} D_{{2,1}} = D_{{0,1}} = D_{{1,2}} = D_{{1,0}} = {b_val}: \quad &-\left[ \frac{{{b_val} - 2D + {b_val}}}{{{h2}}} + \frac{{{b_val} - 2D + {b_val}}}{{{h2}}} \right] = \frac{{{S}}}{{{k}}} \\[6pt]
-\left[ \frac{{-2D}}{{{h2}}} + \frac{{-2D}}{{{h2}}} \right] &= {S / k:.4f} \\[6pt]
-\left[ \frac{{-4D}}{{{h2}}} \right] &= {S / k:.4f} \implies \frac{{4D}}{{{h2}}} = {S / k:.4f} \\[6pt]
{4.0 / h2:.2f} D &= {S / k:.4f} \\[6pt]
D &= \frac{{{S / k:.4f}}}{{{4.0 / h2:.2f}}} = \mathbf{{{centre_dose:.4f}}}
\end{aligned}
"""
    else:
        # General case derivation
        rhs_val = (S * h2) / k
        return rf"""
\begin{aligned}
\text{{General Discrete System for Interior Node }}(i, j): \\[6pt]
&4 D(i, j) - D(i+1, j) - D(i-1, j) - D(i, j+1) - D(i, j-1) = \frac{{S h^2}}{{k}} \\[6pt]
\text{{Parameters: }} k &= {k}, \quad S = {S}, \quad h = {h}, \quad \frac{{S h^2}}{{k}} = {rhs_val:.6f} \\[6pt]
\text{{Solved with }} A \cdot \mathbf{{D}} &= \mathbf{{b}} \quad \text{{via Sparse Linear System}} \\[6pt]
\text{{Computed Centre-Point Dose: }} D_{{\text{{centre}}}} &= \mathbf{{{centre_dose:.6f}}}
\end{aligned}
"""
