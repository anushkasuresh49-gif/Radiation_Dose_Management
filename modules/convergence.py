"""
Module: convergence.py
Grid Convergence and Refinement Analysis comparing FDM and FEM Solvers
Evaluates numerical stability, accuracy, order of convergence, and execution performance as h -> 0.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import time

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False

from .model import ModelParameters, create_grid, validate_parameters
from .fdm_solver import solve_fdm
from .fem_solver import solve_fem
from .validation import calculate_continuous_analytical_solution, calculate_ppt_benchmark


@dataclass
class ComparativeConvergencePoint:
    """Stores comparative result metrics for a specific grid spacing h for both FDM and FEM."""
    grid_spacing: float
    grid_points_total: int
    interior_nodes: int
    triangular_elements: int
    fdm_centre_dose: float
    fem_centre_dose: float
    reference_dose: float
    fdm_absolute_error: float
    fem_absolute_error: float
    fdm_relative_error_pct: float
    fem_relative_error_pct: float
    fdm_execution_time_sec: float
    fem_execution_time_sec: float
    # Backward compatibility attributes
    centre_dose: float = 0.0
    absolute_error: float = 0.0
    relative_error_pct: float = 0.0
    execution_time_sec: float = 0.0

    def __post_init__(self):
        if self.centre_dose == 0.0:
            self.centre_dose = self.fdm_centre_dose
        if self.absolute_error == 0.0:
            self.absolute_error = self.fdm_absolute_error
        if self.relative_error_pct == 0.0:
            self.relative_error_pct = self.fdm_relative_error_pct
        if self.execution_time_sec == 0.0:
            self.execution_time_sec = self.fdm_execution_time_sec


# Backward compatibility alias
ConvergenceDataPoint = ComparativeConvergencePoint


def run_convergence_analysis(
    base_params: ModelParameters,
    spacings: List[float]
) -> List[ComparativeConvergencePoint]:
    """
    Runs full FDM and FEM simulations across a series of grid spacings h.
    Sorts spacings in descending order (coarse to fine) and measures:
    - Grid size & elements
    - Interior unknowns
    - Computed FDM centre dose
    - Computed FEM centre dose
    - Reference exact analytical dose
    - Absolute and relative errors for both methods
    - Measured solver execution times (using time.perf_counter())
    """
    clean_spacings = sorted(list(set(spacings)), reverse=True)
    results: List[ComparativeConvergencePoint] = []

    # Reference exact continuous analytical solution for the domain
    cont_reference_dose = calculate_continuous_analytical_solution(base_params)

    for h_val in clean_spacings:
        run_params = ModelParameters(
            xmin=base_params.xmin,
            xmax=base_params.xmax,
            ymin=base_params.ymin,
            ymax=base_params.ymax,
            k=base_params.k,
            S=base_params.S,
            h=h_val,
            boundary_dose=base_params.boundary_dose
        )

        valid, err = validate_parameters(run_params)
        if not valid:
            continue

        try:
            # 1. FDM Solution
            grid = create_grid(run_params)
            t0_fdm = time.perf_counter()
            fdm_sol = solve_fdm(grid)
            t1_fdm = time.perf_counter()
            fdm_time = max(t1_fdm - t0_fdm, 1e-6)

            # 2. FEM Solution
            t0_fem = time.perf_counter()
            fem_sol = solve_fem(run_params)
            t1_fem = time.perf_counter()
            fem_time = max(t1_fem - t0_fem, 1e-6)

            # 3. Errors evaluated against continuous Fourier series reference
            fdm_abs_err = abs(fdm_sol.centre_dose - cont_reference_dose)
            fem_abs_err = abs(fem_sol.centre_dose - cont_reference_dose)

            fdm_rel_err = (fdm_abs_err / abs(cont_reference_dose) * 100.0) if abs(cont_reference_dose) > 1e-12 else 0.0
            fem_rel_err = (fem_abs_err / abs(cont_reference_dose) * 100.0) if abs(cont_reference_dose) > 1e-12 else 0.0

            results.append(ComparativeConvergencePoint(
                grid_spacing=h_val,
                grid_points_total=grid.total_nodes,
                interior_nodes=grid.interior_nodes_count,
                triangular_elements=fem_sol.mesh.total_elements,
                fdm_centre_dose=fdm_sol.centre_dose,
                fem_centre_dose=fem_sol.centre_dose,
                reference_dose=cont_reference_dose,
                fdm_absolute_error=fdm_abs_err,
                fem_absolute_error=fem_abs_err,
                fdm_relative_error_pct=fdm_rel_err,
                fem_relative_error_pct=fem_rel_err,
                fdm_execution_time_sec=fdm_time,
                fem_execution_time_sec=fem_time,
                centre_dose=fdm_sol.centre_dose,
                absolute_error=fdm_abs_err,
                relative_error_pct=fdm_rel_err,
                execution_time_sec=fdm_time
            ))
        except Exception:
            continue

    return results


def convergence_to_dataframe(results: List[ComparativeConvergencePoint]):
    """
    Converts comparative convergence results to a clean DataFrame:
    Grid Size | FDM Centre Dose | FEM Centre Dose | Reference | FDM Error | FEM Error | FDM Time | FEM Time
    """
    records = []
    for r in results:
        records.append({
            "Grid Spacing (h)": r.grid_spacing,
            "Total Grid Points": r.grid_points_total,
            "Interior Nodes": r.interior_nodes,
            "FEM Elements": r.triangular_elements,
            "FDM Centre Dose": f"{r.fdm_centre_dose:.6f}",
            "FEM Centre Dose": f"{r.fem_centre_dose:.6f}",
            "Analytical Ref": f"{r.reference_dose:.6f}",
            "FDM Absolute Error": f"{r.fdm_absolute_error:.6f}",
            "FEM Absolute Error": f"{r.fem_absolute_error:.6f}",
            "FDM Time (ms)": f"{r.fdm_execution_time_sec * 1000:.3f}",
            "FEM Time (ms)": f"{r.fem_execution_time_sec * 1000:.3f}"
        })
    if HAS_PANDAS:
        return pd.DataFrame(records)
    return records
