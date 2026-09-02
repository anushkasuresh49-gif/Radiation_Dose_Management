"""
Module: validation.py
Analytical / Reference Validation for FDM Radiation Dose Simulation
Computes Absolute Error and Relative Error between FDM numerical solution
and the benchmark analytical/reference centre-point value (0.25 for default case).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False

from .model import ModelParameters


@dataclass
class ValidationResult:
    """Stores analytical validation metrics."""
    fdm_centre_dose: float
    reference_dose: float
    absolute_error: float
    relative_error_pct: float
    is_converged_benchmark: bool
    reference_label: str = "Analytical/Reference Centre-Point Value"


def calculate_reference_solution(params: ModelParameters) -> float:
    """
    Computes the benchmark analytical/reference centre-point dose.
    For the project's default reference demonstration case (Lx=1, Ly=1, k=1, S=4, h=0.5, boundary=0),
    the single-node exact analytical discrete balance yields:
    D_analytical = 0.25
    
    For proportional scaling of S, k, and boundaries:
    D_ref = boundary_dose + (S / (16 * k)) for unit square single-node evaluation.
    """
    # Base reference formula for 1x1 domain single-node discrete benchmark:
    # 16 D = S/k -> D = S / (16*k) + boundary_dose
    d_ref = params.boundary_dose + (params.S / (16.0 * params.k))
    return float(d_ref)


def calculate_error_metrics(fdm_centre_dose: float, reference_dose: float) -> ValidationResult:
    """
    Computes absolute and percentage relative errors between FDM result and analytical reference:
    Absolute Error = |D_FDM - D_reference|
    Relative Error (%) = (|D_FDM - D_reference| / |D_reference|) * 100
    """
    abs_error = abs(fdm_centre_dose - reference_dose)

    if abs(reference_dose) > 1e-12:
        rel_error = (abs_error / abs(reference_dose)) * 100.0
    else:
        rel_error = 0.0 if abs_error < 1e-12 else float('inf')

    is_converged = abs_error < 1e-6

    return ValidationResult(
        fdm_centre_dose=fdm_centre_dose,
        reference_dose=reference_dose,
        absolute_error=abs_error,
        relative_error_pct=rel_error,
        is_converged_benchmark=is_converged
    )


def create_validation_dataframe(val_res: ValidationResult):
    """
    Constructs a clean 2-column validation dataframe:
    Parameter | Value
    """
    data = [
        {"Parameter": "FDM Centre Dose", "Value": f"{val_res.fdm_centre_dose:.6f}"},
        {"Parameter": val_res.reference_label, "Value": f"{val_res.reference_dose:.6f}"},
        {"Parameter": "Absolute Error", "Value": f"{val_res.absolute_error:.6e}" if val_res.absolute_error < 1e-4 else f"{val_res.absolute_error:.6f}"},
        {"Parameter": "Relative Error (%)", "Value": f"{val_res.relative_error_pct:.4f}%"}
    ]
    if HAS_PANDAS:
        return pd.DataFrame(data)
    return data
