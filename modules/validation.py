"""
Module: validation.py
Analytical, Benchmark, and Cross-Method Validation for FDM and FEM Radiation Solvers

Distinguishes clearly between:
1. PPT Benchmark:
   For the specified capstone PPT case (Lx=1, Ly=1, S=4, k=1, h=0.5, Db=0),
   the exact single-interior-node balance yields D_centre = 0.25.
   Formula: D = Db + (S * h^2) / (4 * k)
2. Continuous Analytical Solution (Double Fourier Series):
   Exact infinite-series solution for the elliptic PDE -k ∇²D = S on [0, Lx] x [0, Ly]:
   D_exact(x,y) = Db + ∑_{m,n odd} [16 S / (k π^4 m n (m²/Lx² + n²/Ly²))] * sin(mπx/Lx) * sin(nπy/Ly)
   For unit square with S=4, k=1, this converges to ~0.294690 at centre (0.5, 0.5).
3. Numerical FDM Solution (5-point finite difference stencil).
4. Numerical FEM Solution (3-node linear triangular finite element method).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import math

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False

from .model import ModelParameters


@dataclass
class ValidationResult:
    """Stores analytical, benchmark, and comparative error metrics for FDM and FEM."""
    fdm_centre_dose: float
    fem_centre_dose: float
    ppt_benchmark: float
    continuous_analytical_dose: float
    # PPT Benchmark comparisons
    fdm_vs_ppt_abs_error: float
    fdm_vs_ppt_rel_error_pct: float
    fem_vs_ppt_abs_error: float
    fem_vs_ppt_rel_error_pct: float
    # Continuous Analytical comparisons
    fdm_vs_ana_abs_error: float
    fdm_vs_ana_rel_error_pct: float
    fem_vs_ana_abs_error: float
    fem_vs_ana_rel_error_pct: float
    # Backward compatibility fields
    reference_dose: float
    absolute_error: float
    relative_error_pct: float
    is_converged_benchmark: bool
    reference_label: str = "PPT Reference Benchmark (0.25)"


def calculate_ppt_benchmark(params: ModelParameters) -> float:
    """
    Computes the PPT benchmark dose for a single interior node:
    At single interior node with 4 equal Dirichlet boundaries:
    4 D - 4 D_b = (S * h^2) / k  ==>  D = D_b + (S * h^2) / (4 * k)
    For h=0.5, Lx=1, Ly=1, S=4, k=1:
    D = 0 + (4 * 0.25) / (4 * 1) = 1.0 / 4 = 0.25.
    """
    d_ppt = params.boundary_dose + (params.S * (params.h ** 2)) / (4.0 * params.k)
    return float(d_ppt)


def calculate_continuous_analytical_solution(
    params: ModelParameters,
    x: Optional[float] = None,
    y: Optional[float] = None,
    num_terms: int = 51
) -> float:
    """
    Computes the exact 2D continuous Poisson boundary value solution
    via double Fourier series expansion for -k ∇²D = S on [xmin, xmax] x [ymin, ymax]
    with Dirichlet boundary condition D = D_b on all edges.
    """
    Lx = params.Lx
    Ly = params.Ly
    if x is None:
        x = params.xmin + Lx / 2.0
    if y is None:
        y = params.ymin + Ly / 2.0

    # Local coordinates within [0, Lx] and [0, Ly]
    x_local = x - params.xmin
    y_local = y - params.ymin

    k = params.k
    S = params.S
    pi = math.pi
    pi4 = pi ** 4

    series_sum = 0.0
    for m in range(1, num_terms, 2):
        m2_lx2 = (m / Lx) ** 2
        sin_m = math.sin(m * pi * x_local / Lx)
        for n in range(1, num_terms, 2):
            n2_ly2 = (n / Ly) ** 2
            denom = pi4 * m * n * (m2_lx2 + n2_ly2)
            coeff = (16.0 * S) / (k * denom)
            sin_n = math.sin(n * pi * y_local / Ly)
            series_sum += coeff * sin_m * sin_n

    return float(params.boundary_dose + series_sum)


def calculate_reference_solution(params: ModelParameters) -> float:
    """
    Provides the reference solution based on context:
    - If h=0.5 on unit square: returns PPT benchmark 0.25
    - For general refined grids: returns the continuous analytical Fourier solution
    """
    if abs(params.h - 0.5) < 1e-4 and abs(params.Lx - 1.0) < 1e-4 and abs(params.Ly - 1.0) < 1e-4:
        return calculate_ppt_benchmark(params)
    return calculate_continuous_analytical_solution(params)


def calculate_error_metrics(
    fdm_centre_dose: float,
    reference_dose: float,
    fem_centre_dose: Optional[float] = None,
    params: Optional[ModelParameters] = None
) -> ValidationResult:
    """
    Calculates comprehensive analytical validation metrics comparing FDM, FEM,
    the PPT benchmark (0.25), and the continuous analytical Fourier solution.
    """
    if fem_centre_dose is None:
        fem_centre_dose = fdm_centre_dose

    if params is not None:
        ppt_bench = calculate_ppt_benchmark(params)
        cont_ana = calculate_continuous_analytical_solution(params)
    else:
        ppt_bench = reference_dose
        cont_ana = reference_dose

    # Error vs PPT Benchmark
    fdm_ppt_abs = abs(fdm_centre_dose - ppt_bench)
    fdm_ppt_rel = (fdm_ppt_abs / abs(ppt_bench) * 100.0) if abs(ppt_bench) > 1e-12 else 0.0

    fem_ppt_abs = abs(fem_centre_dose - ppt_bench)
    fem_ppt_rel = (fem_ppt_abs / abs(ppt_bench) * 100.0) if abs(ppt_bench) > 1e-12 else 0.0

    # Error vs Continuous Analytical Solution
    fdm_ana_abs = abs(fdm_centre_dose - cont_ana)
    fdm_ana_rel = (fdm_ana_abs / abs(cont_ana) * 100.0) if abs(cont_ana) > 1e-12 else 0.0

    fem_ana_abs = abs(fem_centre_dose - cont_ana)
    fem_ana_rel = (fem_ana_abs / abs(cont_ana) * 100.0) if abs(cont_ana) > 1e-12 else 0.0

    # Default reference comparison
    abs_error = abs(fdm_centre_dose - reference_dose)
    rel_error = (abs_error / abs(reference_dose) * 100.0) if abs(reference_dose) > 1e-12 else 0.0
    is_converged = abs_error < 1e-6

    return ValidationResult(
        fdm_centre_dose=fdm_centre_dose,
        fem_centre_dose=fem_centre_dose,
        ppt_benchmark=ppt_bench,
        continuous_analytical_dose=cont_ana,
        fdm_vs_ppt_abs_error=fdm_ppt_abs,
        fdm_vs_ppt_rel_error_pct=fdm_ppt_rel,
        fem_vs_ppt_abs_error=fem_ppt_abs,
        fem_vs_ppt_rel_error_pct=fem_ppt_rel,
        fdm_vs_ana_abs_error=fdm_ana_abs,
        fdm_vs_ana_rel_error_pct=fdm_ana_rel,
        fem_vs_ana_abs_error=fem_ana_abs,
        fem_vs_ana_rel_error_pct=fem_ana_rel,
        reference_dose=reference_dose,
        absolute_error=abs_error,
        relative_error_pct=rel_error,
        is_converged_benchmark=is_converged,
        reference_label="PPT Reference Benchmark (0.25)" if abs(reference_dose - 0.25) < 1e-3 else "Analytical Reference"
    )


def create_validation_dataframe(val_res: ValidationResult):
    """
    Constructs a detailed multi-method validation table.
    """
    data = [
        {"Benchmark / Solution Method": "FDM Numerical Solution", "Centre-Point Dose": f"{val_res.fdm_centre_dose:.6f}", "Error vs PPT Benchmark": f"{val_res.fdm_vs_ppt_abs_error:.6f} ({val_res.fdm_vs_ppt_rel_error_pct:.2f}%)", "Error vs Continuous Analytical": f"{val_res.fdm_vs_ana_abs_error:.6f} ({val_res.fdm_vs_ana_rel_error_pct:.2f}%)"},
        {"Benchmark / Solution Method": "FEM Numerical Solution", "Centre-Point Dose": f"{val_res.fem_centre_dose:.6f}", "Error vs PPT Benchmark": f"{val_res.fem_vs_ppt_abs_error:.6f} ({val_res.fem_vs_ppt_rel_error_pct:.2f}%)", "Error vs Continuous Analytical": f"{val_res.fem_vs_ana_abs_error:.6f} ({val_res.fem_vs_ana_rel_error_pct:.2f}%)"},
        {"Benchmark / Solution Method": "PPT Benchmark (h=0.5)", "Centre-Point Dose": f"{val_res.ppt_benchmark:.6f}", "Error vs PPT Benchmark": "0.000000 (Reference)", "Error vs Continuous Analytical": f"{abs(val_res.ppt_benchmark - val_res.continuous_analytical_dose):.6f}"},
        {"Benchmark / Solution Method": "Continuous Analytical (Fourier Series)", "Centre-Point Dose": f"{val_res.continuous_analytical_dose:.6f}", "Error vs PPT Benchmark": f"{abs(val_res.continuous_analytical_dose - val_res.ppt_benchmark):.6f}", "Error vs Continuous Analytical": "0.000000 (Exact Limit)"}
    ]
    if HAS_PANDAS:
        return pd.DataFrame(data)
    return data
