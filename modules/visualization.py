"""
Module: visualization.py
Plotly-based Interactive Visualizations for Radiation Dose Simulation
Generates:
- Structured Grid node map (boundary, interior, centre)
- 2D Dose Heatmap with centre marker and hover values
- 2D Isodose Contour Map
- 3D Interactive Surface Plot
- Convergence multi-panel graphs
- Sensitivity trend charts
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Any
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    go = None
    make_subplots = None
    HAS_PLOTLY = False

from .model import ComputationalGrid
from .fdm_solver import FDMSolution
from .convergence import ConvergenceDataPoint
from .sensitivity import SensitivityResult


# Professional Academic Styling Palette
PRIMARY_BLUE = "#1e3a8a"
ACCENT_CYAN = "#0284c7"
CENTRE_GOLD = "#d97706"
BOUNDARY_GRAY = "#64748b"
INTERIOR_TEAL = "#0d9488"


def create_grid_plot(grid: ComputationalGrid) -> go.Figure:
    """
    Generates interactive 2D scatter visualization of computational domain grid.
    Distinguishes boundary, interior, and centre nodes with clear hover data.
    """
    fig = go.Figure()

    bx, by = [], []
    ix, iy = [], []
    cx, cy = [], []

    Nx = grid.Nx
    Ny = grid.Ny

    for j in range(Ny):
        for i in range(Nx):
            x = grid.x_coords[i]
            y = grid.y_coords[j]
            ntype = grid.node_types[j][i]
            if ntype == "boundary":
                bx.append(x)
                by.append(y)
            elif ntype == "centre":
                cx.append(x)
                cy.append(y)
            else:
                ix.append(x)
                iy.append(y)

    # Boundary nodes
    fig.add_trace(go.Scatter(
        x=bx, y=by,
        mode="markers",
        name=f"Boundary Nodes (D={grid.params.boundary_dose})",
        marker=dict(size=9, color=BOUNDARY_GRAY, symbol="square", line=dict(width=1, color="#334155")),
        hovertemplate="<b>Boundary Node</b><br>X: %{x:.4f}<br>Y: %{y:.4f}<br>Dose: " + f"{grid.params.boundary_dose}<extra></extra>"
    ))

    # Interior nodes
    if ix:
        fig.add_trace(go.Scatter(
            x=ix, y=iy,
            mode="markers",
            name="Interior Nodes (Unknowns)",
            marker=dict(size=10, color=INTERIOR_TEAL, symbol="circle", line=dict(width=1, color="#042f2e")),
            hovertemplate="<b>Interior Node</b><br>X: %{x:.4f}<br>Y: %{y:.4f}<extra></extra>"
        ))

    # Centre node
    if cx:
        fig.add_trace(go.Scatter(
            x=cx, y=cy,
            mode="markers",
            name="Centre Node (Evaluation Point)",
            marker=dict(size=14, color=CENTRE_GOLD, symbol="star", line=dict(width=1.5, color="#78350f")),
            hovertemplate="<b>Domain Centre Node</b><br>X: %{x:.4f}<br>Y: %{y:.4f}<extra></extra>"
        ))

    # Grid line overlays
    for x in grid.x_coords:
        fig.add_shape(type="line", x0=x, x1=x, y0=grid.params.ymin, y1=grid.params.ymax,
                      line=dict(color="#cbd5e1", width=1, dash="dot"))
    for y in grid.y_coords:
        fig.add_shape(type="line", x0=grid.params.xmin, x1=grid.params.xmax, y0=y, y1=y,
                      line=dict(color="#cbd5e1", width=1, dash="dot"))

    fig.update_layout(
        title=dict(text="Structured Computational Domain Grid", x=0.5, font=dict(size=16)),
        xaxis=dict(title="X Coordinate", range=[grid.params.xmin - 0.05, grid.params.xmax + 0.05], constrain="domain"),
        yaxis=dict(title="Y Coordinate", range=[grid.params.ymin - 0.05, grid.params.ymax + 0.05], scaleanchor="x", scaleratio=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        height=480
    )
    return fig


def create_heatmap(sol: FDMSolution) -> go.Figure:
    """
    2D Dose Heatmap with colorbar, hover values, and domain centre marker.
    """
    grid = sol.grid
    ci, cj = grid.centre_index
    cx = grid.x_coords[ci]
    cy = grid.y_coords[cj]

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        x=grid.x_coords,
        y=grid.y_coords,
        z=sol.dose_matrix,
        colorscale="Viridis",
        colorbar=dict(title="Dose D", titleside="right", len=0.9),
        hovertemplate="<b>Position</b><br>X: %{x:.4f}<br>Y: %{y:.4f}<br><b>Dose: %{z:.6f}</b><extra></extra>"
    ))

    # Centre-point marker
    fig.add_trace(go.Scatter(
        x=[cx], y=[cy],
        mode="markers+text",
        name="Centre Point",
        text=["Centre Node"],
        textposition="top center",
        textfont=dict(color="white", size=11),
        marker=dict(size=14, color="#f43f5e", symbol="cross", line=dict(width=2, color="white")),
        hovertemplate=f"<b>Centre Point</b><br>X: {cx:.4f}<br>Y: {cy:.4f}<br>Dose: {sol.centre_dose:.6f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="2D Radiation Dose Distribution Heatmap", x=0.5, font=dict(size=16)),
        xaxis=dict(title="X Coordinate (Spatial)", constrain="domain"),
        yaxis=dict(title="Y Coordinate (Spatial)", scaleanchor="x", scaleratio=1),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=520
    )
    return fig


def create_contour_plot(sol: FDMSolution) -> go.Figure:
    """
    Interactive 2D Isodose Contour Map with labeled isolines.
    """
    grid = sol.grid
    fig = go.Figure()

    fig.add_trace(go.Contour(
        x=grid.x_coords,
        y=grid.y_coords,
        z=sol.dose_matrix,
        colorscale="Turbo",
        contours=dict(
            coloring="heatmap",
            showlabels=True,
            labelfont=dict(size=11, color="white")
        ),
        colorbar=dict(title="Isodose Level", titleside="right"),
        hovertemplate="X: %{x:.4f}<br>Y: %{y:.4f}<br>Dose: %{z:.6f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="Isodose Contour Distribution", x=0.5, font=dict(size=16)),
        xaxis=dict(title="X Coordinate", constrain="domain"),
        yaxis=dict(title="Y Coordinate", scaleanchor="x", scaleratio=1),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=520
    )
    return fig


def create_3d_surface(sol: FDMSolution) -> go.Figure:
    """
    3D Interactive Surface Plot representing radiation dose elevation over domain.
    """
    grid = sol.grid
    fig = go.Figure()

    fig.add_trace(go.Surface(
        x=grid.x_coords,
        y=grid.y_coords,
        z=sol.dose_matrix,
        colorscale="Plasma",
        colorbar=dict(title="Dose D", titleside="right"),
        hovertemplate="X: %{x:.4f}<br>Y: %{y:.4f}<br>Dose: %{z:.6f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="3D Radiation Dose Surface Topology", x=0.5, font=dict(size=16)),
        scene=dict(
            xaxis_title="X Coordinate",
            yaxis_title="Y Coordinate",
            zaxis_title="Radiation Dose D",
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2))
        ),
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        height=560
    )
    return fig


def create_convergence_plots(conv_data: List[ConvergenceDataPoint]) -> go.Figure:
    """
    Generates a 2x2 subplot matrix showing grid convergence metrics:
    - h vs centre dose
    - h vs absolute error
    - h vs relative error (%)
    - h vs execution time (ms)
    """
    sorted_data = sorted(conv_data, key=lambda x: x.grid_spacing)
    h_vals = [d.grid_spacing for d in sorted_data]
    doses = [d.centre_dose for d in sorted_data]
    abs_errs = [d.absolute_error for d in sorted_data]
    rel_errs = [d.relative_error_pct for d in sorted_data]
    times_ms = [d.execution_time_sec * 1000 for d in sorted_data]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Grid Spacing vs Centre Dose",
            "Grid Spacing vs Absolute Error",
            "Grid Spacing vs Relative Error (%)",
            "Grid Spacing vs Execution Time (ms)"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )

    # 1. h vs Centre Dose
    fig.add_trace(go.Scatter(
        x=h_vals, y=doses, mode="lines+markers",
        marker=dict(size=8, color="#1e3a8a"),
        name="Centre Dose",
        hovertemplate="h: %{x}<br>Centre Dose: %{y:.6f}<extra></extra>"
    ), row=1, col=1)

    # 2. h vs Absolute Error
    fig.add_trace(go.Scatter(
        x=h_vals, y=abs_errs, mode="lines+markers",
        marker=dict(size=8, color="#dc2626"),
        name="Absolute Error",
        hovertemplate="h: %{x}<br>Abs Error: %{y:.6e}<extra></extra>"
    ), row=1, col=2)

    # 3. h vs Relative Error
    fig.add_trace(go.Scatter(
        x=h_vals, y=rel_errs, mode="lines+markers",
        marker=dict(size=8, color="#ea580c"),
        name="Relative Error (%)",
        hovertemplate="h: %{x}<br>Rel Error: %{y:.4f}%<extra></extra>"
    ), row=2, col=1)

    # 4. h vs Execution Time
    fig.add_trace(go.Scatter(
        x=h_vals, y=times_ms, mode="lines+markers",
        marker=dict(size=8, color="#059669"),
        name="Execution Time (ms)",
        hovertemplate="h: %{x}<br>Time: %{y:.3f} ms<extra></extra>"
    ), row=2, col=2)

    fig.update_xaxes(title_text="Grid Spacing h", row=1, col=1)
    fig.update_xaxes(title_text="Grid Spacing h", row=1, col=2)
    fig.update_xaxes(title_text="Grid Spacing h", row=2, col=1)
    fig.update_xaxes(title_text="Grid Spacing h", row=2, col=2)

    fig.update_yaxes(title_text="Dose D", row=1, col=1)
    fig.update_yaxes(title_text="|Error|", row=1, col=2)
    fig.update_yaxes(title_text="Error (%)", row=2, col=1)
    fig.update_yaxes(title_text="Time (ms)", row=2, col=2)

    fig.update_layout(
        template="plotly_white",
        height=620,
        showlegend=False,
        margin=dict(l=50, r=40, t=60, b=50)
    )
    return fig


def create_sensitivity_plots(sens: SensitivityResult) -> go.Figure:
    """
    Generates 3-panel sensitivity comparison plots:
    - k vs Centre Dose
    - S vs Centre Dose
    - h vs Centre Dose
    """
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=(
            "Diffusion Coeff. k vs Centre Dose",
            "Source Intensity S vs Centre Dose",
            "Grid Spacing h vs Centre Dose"
        ),
        horizontal_spacing=0.1
    )

    # k vs Dose
    fig.add_trace(go.Scatter(
        x=sens.k_values, y=sens.k_centre_doses,
        mode="lines+markers",
        marker=dict(size=8, color="#2563eb"),
        name="k Sensitivity",
        hovertemplate="k: %{x}<br>Dose: %{y:.4f}<extra></extra>"
    ), row=1, col=1)

    # S vs Dose
    fig.add_trace(go.Scatter(
        x=sens.s_values, y=sens.s_centre_doses,
        mode="lines+markers",
        marker=dict(size=8, color="#0d9488"),
        name="S Sensitivity",
        hovertemplate="S: %{x}<br>Dose: %{y:.4f}<extra></extra>"
    ), row=1, col=2)

    # h vs Dose
    fig.add_trace(go.Scatter(
        x=sens.h_values, y=sens.h_centre_doses,
        mode="lines+markers",
        marker=dict(size=8, color="#7c3aed"),
        name="h Sensitivity",
        hovertemplate="h: %{x}<br>Dose: %{y:.4f}<extra></extra>"
    ), row=1, col=3)

    fig.update_xaxes(title_text="k (Diffusion)", row=1, col=1)
    fig.update_xaxes(title_text="S (Source)", row=1, col=2)
    fig.update_xaxes(title_text="h (Spacing)", row=1, col=3)

    fig.update_yaxes(title_text="Centre Dose D", row=1, col=1)
    fig.update_yaxes(title_text="Centre Dose D", row=1, col=2)
    fig.update_yaxes(title_text="Centre Dose D", row=1, col=3)

    fig.update_layout(
        template="plotly_white",
        height=380,
        showlegend=False,
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig
