"""
Module: convergence.py
Grid Convergence and Refinement Analysis for FDM Radiation Dose Simulation
Evaluates numerical stability, accuracy, and execution performance as h -> 0.
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
from .validation import calculate_reference_solution, calculate_error_metrics


@dataclass
class ConvergenceDataPoint:
    """Stores result metrics for a specific grid spacing h."""
    grid_spacing: float
    grid_points_total: int
    interior_nodes: int
    centre_dose: float
    absolute_error: float
    relative_error_pct: float
    execution_time_sec: float


def run_convergence_analysis(
    base_params: ModelParameters,
    spacings: List[float]
) -> List[ConvergenceDataPoint]:
    """
    Runs full FDM simulation across a series of grid spacings h.
    Sorts spacings in descending order (coarse to fine) and measures:
    - Grid size
    - Interior unknowns
    - Computed centre-point dose
    - Error relative to benchmark
    - Measured solver execution time (using time.perf_counter())
    """
    clean_spacings = sorted(list(set(spacings)), reverse=True)
    results: List[ConvergenceDataPoint] = []

    reference_dose = calculate_reference_solution(base_params)

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
            grid = create_grid(run_params)
            t0 = time.perf_counter()
            sol = solve_fdm(grid)
            t1 = time.perf_counter()
            exec_time = max(t1 - t0, 1e-6)

            err_metrics = calculate_error_metrics(sol.centre_dose, reference_dose)

            results.append(ConvergenceDataPoint(
                grid_spacing=h_val,
                grid_points_total=grid.total_nodes,
                interior_nodes=grid.interior_nodes_count,
                centre_dose=sol.centre_dose,
                absolute_error=err_metrics.absolute_error,
                relative_error_pct=err_metrics.relative_error_pct,
                execution_time_sec=exec_time
            ))
        except Exception:
            continue

    return results


def convergence_to_dataframe(results: List[ConvergenceDataPoint]):
    """Converts convergence results to a clean presentation DataFrame or dict list."""
    records = []
    for r in results:
        records.append({
            "Grid Spacing (h)": r.grid_spacing,
            "Total Grid Points": r.grid_points_total,
            "Interior Nodes": r.interior_nodes,
            "Centre Dose": round(r.centre_dose, 6),
            "Absolute Error": f"{r.absolute_error:.6e}" if r.absolute_error < 1e-4 else f"{r.absolute_error:.6f}",
            "Relative Error (%)": f"{r.relative_error_pct:.4f}%",
            "Execution Time (ms)": round(r.execution_time_sec * 1000, 3)
        })
    if HAS_PANDAS:
        return pd.DataFrame(records)
    return records
