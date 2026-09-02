"""
Radiation Dose Distribution Optimization
Modules Package Initialization
"""

from .model import ModelParameters, ComputationalGrid, create_grid, validate_parameters
from .fdm_solver import (
    FDMSolution,
    build_fdm_system,
    solve_fdm,
    reconstruct_dose_matrix,
    calculate_dose_statistics,
    extract_centre_dose,
    generate_step_by_step_latex
)
from .validation import (
    ValidationResult,
    calculate_reference_solution,
    calculate_error_metrics
)
from .convergence import (
    ConvergenceDataPoint,
    run_convergence_analysis
)
from .sensitivity import (
    SensitivityResult,
    run_sensitivity_analysis
)
from .visualization import (
    create_grid_plot,
    create_heatmap,
    create_contour_plot,
    create_3d_surface,
    create_convergence_plots,
    create_sensitivity_plots
)
from .report import (
    generate_summary_dataframe,
    generate_csv_report,
    generate_pdf_report,
    generate_academic_interpretation
)

__all__ = [
    "ModelParameters",
    "ComputationalGrid",
    "create_grid",
    "validate_parameters",
    "FDMSolution",
    "build_fdm_system",
    "solve_fdm",
    "reconstruct_dose_matrix",
    "calculate_dose_statistics",
    "extract_centre_dose",
    "generate_step_by_step_latex",
    "ValidationResult",
    "calculate_reference_solution",
    "calculate_error_metrics",
    "ConvergenceDataPoint",
    "run_convergence_analysis",
    "SensitivityResult",
    "run_sensitivity_analysis",
    "create_grid_plot",
    "create_heatmap",
    "create_contour_plot",
    "create_3d_surface",
    "create_convergence_plots",
    "create_sensitivity_plots",
    "generate_summary_dataframe",
    "generate_csv_report",
    "generate_pdf_report",
    "generate_academic_interpretation"
]
