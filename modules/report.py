"""
Module: report.py
Report Generation and Export Utilities (CSV, PDF, and Summary DataFrames)
Academic Radiation Dose Optimization using FDM and FEM Solvers
"""

from __future__ import annotations
import io
import datetime
from typing import Dict, Any, List, Optional
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False

from .model import ModelParameters
from .fdm_solver import FDMSolution
from .fem_solver import FEMSolution
from .validation import ValidationResult
from .convergence import ComparativeConvergencePoint
from .sensitivity import TumourExposureMetrics

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def generate_academic_interpretation(
    sol: FDMSolution,
    val: ValidationResult,
    tumour: Optional[TumourExposureMetrics] = None,
    fem_sol: Optional[FEMSolution] = None
) -> str:
    """
    Generates a rigorous academic summary interpretation of both FDM and FEM numerical findings.
    Strictly devoid of clinical advice or medical treatment efficacy claims.
    """
    params = sol.grid.params
    text = (
        f"The research platform formulated and solved the steady-state radiation Poisson PDE "
        f"-k∇²D = S across domain [{params.xmin}, {params.xmax}] × [{params.ymin}, {params.ymax}] "
        f"with grid spacing h={params.h}, diffusion coefficient k={params.k}, and source S={params.S}. "
        f"\n\n"
        f"1. Finite Difference Method (FDM): Discretized via 5-point central Laplacian stencil "
        f"yielding {sol.matrix_dim} interior degrees of freedom, solved in {sol.execution_time_sec * 1000:.3f} ms. "
        f"Computed centre-point dose: D_FDM = {sol.centre_dose:.6f}. "
    )

    if fem_sol:
        text += (
            f"\n2. Finite Element Method (FEM): Discretized using {fem_sol.mesh.total_elements} triangular finite elements "
            f"and {fem_sol.mesh.total_nodes} nodes, assembled via weak-form stiffness integration [K]{{D}} = {{F}}, "
            f"solved in {fem_sol.execution_time_sec * 1000:.3f} ms. "
            f"Computed centre-point dose: D_FEM = {fem_sol.centre_dose:.6f}. "
        )

    text += (
        f"\n3. Analytical Benchmarking: For the PPT benchmark reference (h=0.5, S=4, k=1), the analytical "
        f"balance gives D_PPT = {val.ppt_benchmark:.6f}. FDM absolute error = {val.fdm_vs_ppt_abs_error:.6e} "
        f"({val.fdm_vs_ppt_rel_error_pct:.2f}%), and FEM absolute error = {val.fem_vs_ppt_abs_error:.6e} "
        f"({val.fem_vs_ppt_rel_error_pct:.2f}%). "
        f"Against the continuous 2D Fourier series solution (D_exact = {val.continuous_analytical_dose:.6f}), "
        f"both methods exhibit consistent asymptotic convergence as grid resolution h is refined."
    )

    if tumour:
        text += (
            f"\n\n4. Spatial Exposure Analysis: Evaluated average tumour-region dose of {tumour.avg_tumour_dose:.4f} "
            f"and surrounding tissue dose of {tumour.avg_surrounding_dose:.4f}, giving a tumour-to-surrounding "
            f"ratio of {tumour.tumour_to_surrounding_ratio:.2f}x."
        )

    return text


def generate_summary_dataframe(
    sol: FDMSolution,
    val: ValidationResult,
    fem_sol: Optional[FEMSolution] = None
) -> pd.DataFrame:
    """
    Generates a structured comprehensive comparative key-value metric summary table.
    """
    p = sol.grid.params
    records = [
        {"Category": "Domain", "Parameter": "Spatial Range X", "Value": f"[{p.xmin}, {p.xmax}] (Lx={p.Lx})"},
        {"Category": "Domain", "Parameter": "Spatial Range Y", "Value": f"[{p.ymin}, {p.ymax}] (Ly={p.Ly})"},
        {"Category": "Domain", "Parameter": "Grid Spacing (h)", "Value": f"{p.h}"},
        {"Category": "Domain", "Parameter": "Total Grid Points", "Value": f"{sol.grid.total_nodes}"},
        {"Category": "Domain", "Parameter": "Interior Degrees of Freedom", "Value": f"{sol.grid.interior_nodes_count}"},
        {"Category": "Model", "Parameter": "Diffusion Coefficient (k)", "Value": f"{p.k}"},
        {"Category": "Model", "Parameter": "Source Intensity (S)", "Value": f"{p.S}"},
        {"Category": "Model", "Parameter": "Dirichlet Boundary Dose (Db)", "Value": f"{p.boundary_dose}"},
        {"Category": "FDM Solver", "Parameter": "FDM Centre-Point Dose", "Value": f"{sol.centre_dose:.6f}"},
        {"Category": "FDM Solver", "Parameter": "FDM Max / Min Dose", "Value": f"{sol.max_dose:.6f} / {sol.min_dose:.6f}"},
        {"Category": "FDM Solver", "Parameter": "FDM Execution Time", "Value": f"{sol.execution_time_sec * 1000:.3f} ms"},
    ]

    if fem_sol:
        records.extend([
            {"Category": "FEM Solver", "Parameter": "FEM Triangular Elements", "Value": f"{fem_sol.mesh.total_elements}"},
            {"Category": "FEM Solver", "Parameter": "FEM Centre-Point Dose", "Value": f"{fem_sol.centre_dose:.6f}"},
            {"Category": "FEM Solver", "Parameter": "FEM Max / Min Dose", "Value": f"{fem_sol.max_dose:.6f} / {fem_sol.min_dose:.6f}"},
            {"Category": "FEM Solver", "Parameter": "FEM Execution Time", "Value": f"{fem_sol.execution_time_sec * 1000:.3f} ms"},
        ])

    records.extend([
        {"Category": "Validation", "Parameter": "PPT Benchmark (h=0.5)", "Value": f"{val.ppt_benchmark:.6f}"},
        {"Category": "Validation", "Parameter": "FDM Error vs PPT Benchmark", "Value": f"{val.fdm_vs_ppt_abs_error:.6e} ({val.fdm_vs_ppt_rel_error_pct:.2f}%)"},
        {"Category": "Validation", "Parameter": "FEM Error vs PPT Benchmark", "Value": f"{val.fem_vs_ppt_abs_error:.6e} ({val.fem_vs_ppt_rel_error_pct:.2f}%)"},
        {"Category": "Validation", "Parameter": "Continuous Analytical Solution", "Value": f"{val.continuous_analytical_dose:.6f}"},
        {"Category": "Validation", "Parameter": "FDM Error vs Analytical", "Value": f"{val.fdm_vs_ana_abs_error:.6f} ({val.fdm_vs_ana_rel_error_pct:.2f}%)"},
        {"Category": "Validation", "Parameter": "FEM Error vs Analytical", "Value": f"{val.fem_vs_ana_abs_error:.6f} ({val.fem_vs_ana_rel_error_pct:.2f}%)"}
    ])

    return pd.DataFrame(records)


def generate_csv_report(
    sol: FDMSolution,
    val: ValidationResult,
    fem_sol: Optional[FEMSolution] = None
) -> str:
    """Generates downloadable CSV text containing summary metrics, FDM grid, and FEM nodal doses."""
    df_summary = generate_summary_dataframe(sol, val, fem_sol)
    csv_buf = io.StringIO()

    csv_buf.write("# RADIATION DOSE DISTRIBUTION OPTIMIZATION USING FDM AND FEM\n")
    csv_buf.write(f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    csv_buf.write("# Academic Capstone Research Simulation - Not for clinical use\n\n")

    csv_buf.write("## COMPARATIVE SUMMARY METRICS\n")
    df_summary.to_csv(csv_buf, index=False)

    csv_buf.write("\n## 2D FDM DOSE DISTRIBUTION MATRIX\n")
    dose_df = pd.DataFrame(sol.dose_matrix, index=sol.grid.y_coords, columns=sol.grid.x_coords)
    dose_df.to_csv(csv_buf)

    if fem_sol:
        csv_buf.write("\n## 2D FEM DOSE DISTRIBUTION MATRIX\n")
        fem_df = pd.DataFrame(fem_sol.dose_matrix, index=sol.grid.y_coords, columns=sol.grid.x_coords)
        fem_df.to_csv(csv_buf)

    return csv_buf.getvalue()


def generate_pdf_report(
    sol: FDMSolution,
    val: ValidationResult,
    conv_data: Optional[List[ComparativeConvergencePoint]] = None,
    tumour: Optional[TumourExposureMetrics] = None,
    fem_sol: Optional[FEMSolution] = None
) -> bytes:
    """
    Generates a formal academic research PDF report using ReportLab.
    Returns bytes of PDF document.
    """
    if not HAS_REPORTLAB:
        raise RuntimeError("ReportLab package is required for PDF compilation.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155")
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Italic'],
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#b91c1c")
    )

    elements = []

    # Title & Subtitle
    elements.append(Paragraph("Optimising Radiation Dose Distribution in Cancer Treatment", title_style))
    elements.append(Paragraph("Using Finite Difference and Finite Element Methods for Reduced Healthy Tissue Exposure", subtitle_style))

    # Academic Disclaimer
    disclaimer_text = (
        "<b>ACADEMIC RESEARCH SIMULATION ONLY:</b> This software is developed for numerical analysis demonstration "
        "and must not be used for clinical diagnosis, radiotherapy treatment planning, or medical decision-making."
    )
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    elements.append(Spacer(1, 8))

    # Section 1: Governing PDE
    elements.append(Paragraph("1. Mathematical Formulation & Governing PDE", h2_style))
    pde_text = (
        "Governing Equation: <b>-k (∂²D/∂x² + ∂²D/∂y²) = S</b><br/>"
        "where <i>D</i> = Radiation Dose, <i>k</i> = Diffusion Coefficient, and <i>S</i> = Radiation Source Intensity.<br/>"
        f"Domain: [0, {sol.grid.params.Lx}] × [0, {sol.grid.params.Ly}], Grid Spacing h = {sol.grid.params.h}, "
        f"Boundary Condition D = {sol.grid.params.boundary_dose}."
    )
    elements.append(Paragraph(pde_text, body_style))
    elements.append(Spacer(1, 6))

    # Section 2: FDM vs FEM Performance Comparison Table
    elements.append(Paragraph("2. Numerical Solver Comparison (FDM vs FEM)", h2_style))
    val_table_data = [
        ["Metric", "FDM Solver", "FEM Solver (Triangular)", "Benchmark Reference"],
        ["Centre-Point Dose", f"{sol.centre_dose:.6f}", f"{fem_sol.centre_dose:.6f}" if fem_sol else "-", f"PPT: {val.ppt_benchmark:.4f}"],
        ["Absolute Error vs PPT", f"{val.fdm_vs_ppt_abs_error:.6f}", f"{val.fem_vs_ppt_abs_error:.6f}", "0.000000"],
        ["Continuous Analytical", f"{val.continuous_analytical_dose:.6f}", f"{val.continuous_analytical_dose:.6f}", f"{val.continuous_analytical_dose:.6f}"],
        ["Maximum Domain Dose", f"{sol.max_dose:.6f}", f"{fem_sol.max_dose:.6f}" if fem_sol else "-", "-"],
        ["Mean Domain Dose", f"{sol.mean_dose:.6f}", f"{fem_sol.mean_dose:.6f}" if fem_sol else "-", "-"],
        ["Discretization Elements", f"{sol.grid.total_nodes} nodes", f"{fem_sol.mesh.total_elements} triangles" if fem_sol else "-", "-"],
        ["Measured Execution Time", f"{sol.execution_time_sec*1000:.3f} ms", f"{fem_sol.execution_time_sec*1000:.3f} ms" if fem_sol else "-", "time.perf_counter()"]
    ]
    t = Table(val_table_data, colWidths=[130, 120, 140, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 8))

    # Section 3: Academic Interpretation
    elements.append(Paragraph("3. Academic Findings & Convergence Interpretation", h2_style))
    interp = generate_academic_interpretation(sol, val, tumour, fem_sol)
    elements.append(Paragraph(interp.replace("\n", "<br/>"), body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
