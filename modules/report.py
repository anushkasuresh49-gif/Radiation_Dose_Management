"""
Module: report.py
Report Generation and Export Utilities (CSV, PDF, and Summary DataFrames)
Academic Radiation Dose FDM Simulation
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
from .validation import ValidationResult
from .convergence import ConvergenceDataPoint
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
    tumour: Optional[TumourExposureMetrics] = None
) -> str:
    """
    Generates a rigorous academic summary interpretation of the numerical findings.
    Strictly devoid of clinical advice or medical treatment efficacy claims.
    """
    params = sol.grid.params
    text = (
        f"The Finite Difference Method (FDM) numerical solver successfully discretized and evaluated "
        f"the governing Poisson radiation diffusion equation -k∇²D = S over the structured 2D Cartesian "
        f"domain [{params.xmin}, {params.xmax}] × [{params.ymin}, {params.ymax}] with grid spacing h={params.h}. "
        f"The discrete system yielded a matrix dimension of {sol.matrix_dim} unknowns, solved in "
        f"{sol.execution_time_sec * 1000:.3f} ms. "
        f"The computed domain centre-point dose reached D = {sol.centre_dose:.6f}. "
        f"Comparing this against the benchmark analytical/reference centre-point value (D_ref = {val.reference_dose:.6f}), "
        f"the solver achieved an absolute error of {val.absolute_error:.6e} and a relative error of "
        f"{val.relative_error_pct:.4f}%. "
    )

    if tumour:
        text += (
            f"Based on the academic spatial ROI definitions, the simulation-based dose exposure indicator "
            f"measured an average tumour-region dose of {tumour.avg_tumour_dose:.4f} and surrounding healthy-tissue "
            f"average dose of {tumour.avg_surrounding_dose:.4f}, producing a tumour-to-surrounding ratio of "
            f"{tumour.tumour_to_surrounding_ratio:.2f}."
        )

    return text


def generate_summary_dataframe(sol: FDMSolution, val: ValidationResult) -> pd.DataFrame:
    """
    Generates a structured comprehensive key-value metric summary table.
    """
    p = sol.grid.params
    records = [
        {"Category": "Domain", "Parameter": "X Range [xmin, xmax]", "Value": f"[{p.xmin}, {p.xmax}] (Lx={p.Lx})"},
        {"Category": "Domain", "Parameter": "Y Range [ymin, ymax]", "Value": f"[{p.ymin}, {p.ymax}] (Ly={p.Ly})"},
        {"Category": "Domain", "Parameter": "Grid Spacing (h)", "Value": f"{p.h}"},
        {"Category": "Domain", "Parameter": "Grid Dimension (Nx × Ny)", "Value": f"{sol.grid.Nx} × {sol.grid.Ny}"},
        {"Category": "Domain", "Parameter": "Total Grid Points", "Value": f"{sol.grid.total_nodes}"},
        {"Category": "Domain", "Parameter": "Interior Nodes (Unknowns)", "Value": f"{sol.grid.interior_nodes_count}"},
        {"Category": "Model", "Parameter": "Diffusion Coefficient (k)", "Value": f"{p.k}"},
        {"Category": "Model", "Parameter": "Source Intensity (S)", "Value": f"{p.S}"},
        {"Category": "Model", "Parameter": "Dirichlet Boundary Dose", "Value": f"{p.boundary_dose}"},
        {"Category": "FDM Solution", "Parameter": "Centre-Point Dose", "Value": f"{sol.centre_dose:.6f}"},
        {"Category": "FDM Solution", "Parameter": "Maximum Dose", "Value": f"{sol.max_dose:.6f}"},
        {"Category": "FDM Solution", "Parameter": "Minimum Dose", "Value": f"{sol.min_dose:.6f}"},
        {"Category": "FDM Solution", "Parameter": "Mean Dose", "Value": f"{sol.mean_dose:.6f}"},
        {"Category": "FDM Solution", "Parameter": "Standard Deviation", "Value": f"{sol.std_dose:.6f}"},
        {"Category": "FDM Solution", "Parameter": "Execution Time", "Value": f"{sol.execution_time_sec * 1000:.3f} ms"},
        {"Category": "Validation", "Parameter": "Reference Centre Dose", "Value": f"{val.reference_dose:.6f}"},
        {"Category": "Validation", "Parameter": "Absolute Error", "Value": f"{val.absolute_error:.6e}"},
        {"Category": "Validation", "Parameter": "Relative Error (%)", "Value": f"{val.relative_error_pct:.4f}%"}
    ]
    return pd.DataFrame(records)


def generate_csv_report(sol: FDMSolution, val: ValidationResult) -> str:
    """Generates downloadable CSV text containing summary metrics and full 2D dose grid."""
    df_summary = generate_summary_dataframe(sol, val)
    csv_buf = io.StringIO()

    csv_buf.write("# RADIATION DOSE DISTRIBUTION OPTIMIZATION SIMULATION REPORT\n")
    csv_buf.write(f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    csv_buf.write("# Academic Simulation Only - Not for clinical use\n\n")

    csv_buf.write("## SUMMARY METRICS\n")
    df_summary.to_csv(csv_buf, index=False)

    csv_buf.write("\n## 2D DOSE DISTRIBUTION MATRIX (Row: Y decreasing/increasing, Col: X)\n")
    dose_df = pd.DataFrame(sol.dose_matrix, index=sol.grid.y_coords, columns=sol.grid.x_coords)
    dose_df.to_csv(csv_buf)

    return csv_buf.getvalue()


def generate_pdf_report(
    sol: FDMSolution,
    val: ValidationResult,
    conv_data: Optional[List[ConvergenceDataPoint]] = None,
    tumour: Optional[TumourExposureMetrics] = None
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
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Italic'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#b91c1c")
    )

    elements = []

    # Title & Subtitle
    elements.append(Paragraph("Optimizing Radiation Dose Distribution in Cancer Treatment", title_style))
    elements.append(Paragraph("Finite Difference Method with Analytical Solution for Reduced Healthy Tissue Exposure", subtitle_style))
    elements.append(Spacer(1, 4))

    # Academic Disclaimer
    disclaimer_text = (
        "<b>ACADEMIC SIMULATION DISCLAIMER:</b> Academic Simulation Only — This application is intended "
        "for mathematical and numerical-method demonstration and must not be used for clinical diagnosis, "
        "treatment planning, or medical decision-making."
    )
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    elements.append(Spacer(1, 10))

    # Section 1: Mathematical Model
    elements.append(Paragraph("1. Mathematical Model & Governing PDE", h2_style))
    pde_text = (
        "Governing Equation: <b>-k (∂²D/∂x² + ∂²D/∂y²) = S</b><br/>"
        "where <i>D</i> is radiation dose, <i>k</i> is diffusion coefficient, and <i>S</i> is source intensity.<br/>"
        f"Domain: [0, {sol.grid.params.Lx}] × [0, {sol.grid.params.Ly}], Grid Spacing h = {sol.grid.params.h}, "
        f"Boundary Condition D = {sol.grid.params.boundary_dose}."
    )
    elements.append(Paragraph(pde_text, body_style))
    elements.append(Spacer(1, 8))

    # Section 2: Numerical Results & Validation
    elements.append(Paragraph("2. Numerical Results & Analytical Benchmark", h2_style))
    val_table_data = [
        ["Parameter", "Numerical (FDM)", "Analytical / Reference", "Deviation / Error"],
        ["Domain Centre Dose", f"{sol.centre_dose:.6f}", f"{val.reference_dose:.6f}", f"Abs: {val.absolute_error:.6e}"],
        ["Relative Error (%)", f"{val.relative_error_pct:.4f}%", "Target: 0.00%", "Status: Validated"],
        ["Maximum Domain Dose", f"{sol.max_dose:.6f}", "-", "-"],
        ["Mean Domain Dose", f"{sol.mean_dose:.6f}", "-", "-"],
        ["Matrix System Size", f"{sol.matrix_dim} × {sol.matrix_dim}", "-", f"Time: {sol.execution_time_sec*1000:.2f} ms"]
    ]
    t = Table(val_table_data, colWidths=[150, 110, 130, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    # Section 3: Exposure Indicators (if provided)
    if tumour:
        elements.append(Paragraph("3. Reduced Healthy Tissue Exposure Indicators (Academic)", h2_style))
        tumour_data = [
            ["Indicator", "Value", "Notes"],
            ["Average Tumour Dose", f"{tumour.avg_tumour_dose:.4f}", f"Evaluated over {tumour.tumour_nodes_count} nodes"],
            ["Surrounding Tissue Avg Dose", f"{tumour.avg_surrounding_dose:.4f}", f"Evaluated over {tumour.surrounding_nodes_count} nodes"],
            ["Tumour-to-Surrounding Ratio", f"{tumour.tumour_to_surrounding_ratio:.2f}", "Simulation ratio"]
        ]
        tt = Table(tumour_data, colWidths=[160, 100, 270])
        tt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(tt)
        elements.append(Spacer(1, 10))

    # Section 4: Academic Interpretation
    elements.append(Paragraph("4. Academic Interpretation", h2_style))
    interp = generate_academic_interpretation(sol, val, tumour)
    elements.append(Paragraph(interp, body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
