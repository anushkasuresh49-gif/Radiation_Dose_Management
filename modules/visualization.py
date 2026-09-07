"""
Module: visualization.py
Plotly-based Interactive Visualizations for FDM and FEM Radiation Dose Simulation
Generates:
- Structured Grid node map (boundary, interior, centre)
- Triangular Finite Element Mesh visualization (elements, wireframes, nodes)
- 2D FDM Dose Heatmap and Isodose Contours
- 2D FEM Dose Distribution and Mesh Overlay
- Side-by-side FDM vs FEM Comparative Heatmaps
- 3D Interactive Surface Elevation Plots
- Comparative Convergence Curves (FDM vs FEM vs Continuous Analytical)
- Parameter Sensitivity Trend Charts
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
from .fem_solver import FEMSolution, FEMMesh
from .convergence import ComparativeConvergencePoint
from .sensitivity import SensitivityResult


# Professional Academic Styling Palette
PRIMARY_BLUE = "#1e3a8a"
ACCENT_CYAN = "#0284c7"
CENTRE_GOLD = "#d97706"
BOUNDARY_GRAY = "#64748b"
INTERIOR_TEAL = "#0d9488"


def create_grid_plot(grid: ComputationalGrid) -> go.Figure:
    """
    Generates interactive 2D scatter visualization of FDM computational domain grid.
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
        title=dict(text="FDM Structured Cartesian Computational Grid", x=0.5, font=dict(size=16)),
        xaxis=dict(title="X Coordinate", range=[grid.params.xmin - 0.05, grid.params.xmax + 0.05], constrain="domain"),
        yaxis=dict(title="Y Coordinate", range=[grid.params.ymin - 0.05, grid.params.ymax + 0.05], scaleanchor="x", scaleratio=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        height=480
    )
    return fig


def create_fem_mesh_plot(mesh: FEMMesh, fem_sol: Optional[FEMSolution] = None) -> go.Figure:
    """
    Visualizes the structured 2D triangular finite element mesh with:
    - Triangular element wireframes (element boundaries)
    - Boundary nodes, interior nodes, and central evaluation node
    - Hoverable element indices and node IDs
    """
    fig = go.Figure()

    # 1. Plot element wireframe edges as segmented lines with None delimiters
    edge_x = []
    edge_y = []
    for elem in mesh.elements:
        (v1, v2, v3) = elem.vertices
        edge_x.extend([v1[0], v2[0], v3[0], v1[0], None])
        edge_y.extend([v1[1], v2[1], v3[1], v1[1], None])

    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(color="#94a3b8", width=1),
        name=f"Triangular Elements ({mesh.total_elements})",
        hoverinfo="none"
    ))

    # 2. Nodes by type
    bx, by, b_doses = [], [], []
    ix, iy, i_doses = [], [], []
    cx, cy, c_dose = 0.0, 0.0, 0.0

    for idx, (x, y) in enumerate(mesh.nodes):
        dose_val = fem_sol.nodal_doses[idx] if fem_sol else 0.0
        if idx == mesh.centre_node_index:
            cx, cy, c_dose = x, y, dose_val
        elif mesh.is_boundary[idx]:
            bx.append(x)
            by.append(y)
            b_doses.append(dose_val)
        else:
            ix.append(x)
            iy.append(y)
            i_doses.append(dose_val)

    fig.add_trace(go.Scatter(
        x=bx, y=by,
        mode="markers",
        name=f"Boundary Nodes ({mesh.boundary_nodes_count})",
        marker=dict(size=8, color=BOUNDARY_GRAY, symbol="square", line=dict(width=1, color="#334155")),
        hovertemplate="<b>FEM Boundary Node</b><br>X: %{x:.4f}<br>Y: %{y:.4f}<br>Dose: %{customdata:.6f}<extra></extra>",
        customdata=b_doses
    ))

    if ix:
        fig.add_trace(go.Scatter(
            x=ix, y=iy,
            mode="markers",
            name=f"Interior Nodes ({mesh.interior_nodes_count})",
            marker=dict(size=9, color=INTERIOR_TEAL, symbol="circle", line=dict(width=1, color="#042f2e")),
            hovertemplate="<b>FEM Interior Node</b><br>X: %{x:.4f}<br>Y: %{y:.4f}<br>Dose: %{customdata:.6f}<extra></extra>",
            customdata=i_doses
        ))

    fig.add_trace(go.Scatter(
        x=[cx], y=[cy],
        mode="markers",
        name="Centre Evaluation Node",
        marker=dict(size=14, color=CENTRE_GOLD, symbol="star", line=dict(width=1.5, color="#78350f")),
        hovertemplate=f"<b>FEM Centre Node</b><br>X: {cx:.4f}<br>Y: {cy:.4f}<br>Dose: {c_dose:.6f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=f"FEM Triangular Finite Element Mesh ({mesh.total_elements} Triangles, {mesh.total_nodes} Nodes)", x=0.5, font=dict(size=16)),
        xaxis=dict(title="X Coordinate", constrain="domain"),
        yaxis=dict(title="Y Coordinate", scaleanchor="x", scaleratio=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        height=500
    )
    return fig


def create_fem_dose_plot(fem_sol: FEMSolution) -> go.Figure:
    """
    Interactive 2D FEM Dose Field distribution with triangular mesh element overlay.
    """
    mesh = fem_sol.mesh
    fig = go.Figure()

    # Reconstructed 2D contour/heatmap
    xs = [mesh.nodes[i][0] for i in range(mesh.Nx)]
    ys = [mesh.nodes[j * mesh.Nx][1] for j in range(mesh.Ny)]

    fig.add_trace(go.Contour(
        x=xs,
        y=ys,
        z=fem_sol.dose_matrix,
        colorscale="Viridis",
        contours=dict(coloring="heatmap", showlabels=True),
        colorbar=dict(title="FEM Dose D", titleside="right"),
        hovertemplate="X: %{x:.4f}<br>Y: %{y:.4f}<br><b>FEM Dose: %{z:.6f}</b><extra></extra>"
    ))

    # Centre-point marker
    cx, cy = mesh.centre_coordinates
    fig.add_trace(go.Scatter(
        x=[cx], y=[cy],
        mode="markers+text",
        name="Centre Node",
        text=[f"{fem_sol.centre_dose:.4f}"],
        textposition="top center",
        textfont=dict(color="white", size=11, family="sans-serif"),
        marker=dict(size=14, color="#f43f5e", symbol="cross", line=dict(width=2, color="white")),
        hovertemplate=f"<b>FEM Centre Evaluation Point</b><br>X: {cx:.4f}<br>Y: {cy:.4f}<br>Dose: {fem_sol.centre_dose:.6f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="2D FEM Radiation Dose Distribution (Triangular Elements)", x=0.5, font=dict(size=16)),
        xaxis=dict(title="X Coordinate (Spatial)", constrain="domain"),
        yaxis=dict(title="Y Coordinate (Spatial)", scaleanchor="x", scaleratio=1),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=520
    )
    return fig


def create_heatmap(sol: FDMSolution) -> go.Figure:
    """
    2D FDM Dose Heatmap with colorbar, hover values, and domain centre marker.
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
        colorbar=dict(title="FDM Dose D", titleside="right", len=0.9),
        hovertemplate="<b>Position</b><br>X: %{x:.4f}<br>Y: %{y:.4f}<br><b>Dose: %{z:.6f}</b><extra></extra>"
    ))

    # Centre-point marker
    fig.add_trace(go.Scatter(
        x=[cx], y=[cy],
        mode="markers+text",
        name="Centre Point",
        text=[f"{sol.centre_dose:.4f}"],
        textposition="top center",
        textfont=dict(color="white", size=11),
        marker=dict(size=14, color="#f43f5e", symbol="cross", line=dict(width=2, color="white")),
        hovertemplate=f"<b>Centre Point</b><br>X: {cx:.4f}<br>Y: {cy:.4f}<br>Dose: {sol.centre_dose:.6f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="2D FDM Radiation Dose Distribution Heatmap", x=0.5, font=dict(size=16)),
        xaxis=dict(title="X Coordinate (Spatial)", constrain="domain"),
        yaxis=dict(title="Y Coordinate (Spatial)", scaleanchor="x", scaleratio=1),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=520
    )
    return fig


def create_fdm_vs_fem_comparison_plot(fdm_sol: FDMSolution, fem_sol: FEMSolution) -> go.Figure:
    """
    Side-by-side comparative subplots displaying FDM vs FEM dose distributions with matched color range.
    """
    grid = fdm_sol.grid
    z_min = min(fdm_sol.min_dose, fem_sol.min_dose)
    z_max = max(fdm_sol.max_dose, fem_sol.max_dose)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"FDM Solution (Centre: {fdm_sol.centre_dose:.6f})",
            f"FEM Solution (Centre: {fem_sol.centre_dose:.6f})"
        ),
        horizontal_spacing=0.1
    )

    # 1. FDM Heatmap
    fig.add_trace(go.Heatmap(
        x=grid.x_coords,
        y=grid.y_coords,
        z=fdm_sol.dose_matrix,
        colorscale="Viridis",
        zmin=z_min,
        zmax=z_max,
        coloraxis="coloraxis",
        hovertemplate="FDM<br>X: %{x:.4f}<br>Y: %{y:.4f}<br>Dose: %{z:.6f}<extra></extra>"
    ), row=1, col=1)

    # 2. FEM Heatmap
    fig.add_trace(go.Heatmap(
        x=grid.x_coords,
        y=grid.y_coords,
        z=fem_sol.dose_matrix,
        colorscale="Viridis",
        zmin=z_min,
        zmax=z_max,
        coloraxis="coloraxis",
        hovertemplate="FEM<br>X: %{x:.4f}<br>Y: %{y:.4f}<br>Dose: %{z:.6f}<extra></extra>"
    ), row=1, col=2)

    fig.update_xaxes(title_text="X Coordinate", constrain="domain", row=1, col=1)
    fig.update_xaxes(title_text="X Coordinate", constrain="domain", row=1, col=2)
    fig.update_yaxes(title_text="Y Coordinate", scaleanchor="x", scaleratio=1, row=1, col=1)
    fig.update_yaxes(title_text="Y Coordinate", scaleanchor="x2", scaleratio=1, row=1, col=2)

    fig.update_layout(
        title=dict(text="Side-by-Side Comparison: FDM vs FEM Radiation Dose Distributions", x=0.5, font=dict(size=16)),
        coloraxis=dict(colorscale="Viridis", colorbar=dict(title="Dose D")),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
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


def create_convergence_plots(conv_data: List[ComparativeConvergencePoint]) -> go.Figure:
    """
    Generates a 2x2 subplot matrix comparing FDM and FEM grid convergence metrics:
    - h vs Centre Dose (FDM vs FEM vs Continuous Analytical)
    - h vs Absolute Error (FDM vs FEM)
    - h vs Relative Error (FDM vs FEM)
    - h vs Execution Time (FDM vs FEM)
    """
    sorted_data = sorted(conv_data, key=lambda x: x.grid_spacing)
    h_vals = [d.grid_spacing for d in sorted_data]
    fdm_doses = [d.fdm_centre_dose for d in sorted_data]
    fem_doses = [d.fem_centre_dose for d in sorted_data]
    ref_doses = [d.reference_dose for d in sorted_data]

    fdm_abs = [d.fdm_absolute_error for d in sorted_data]
    fem_abs = [d.fem_absolute_error for d in sorted_data]

    fdm_rel = [d.fdm_relative_error_pct for d in sorted_data]
    fem_rel = [d.fem_relative_error_pct for d in sorted_data]

    fdm_time = [d.fdm_execution_time_sec * 1000 for d in sorted_data]
    fem_time = [d.fem_execution_time_sec * 1000 for d in sorted_data]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Grid Spacing vs Centre Dose (Convergence to Analytical)",
            "Grid Spacing vs Absolute Error |D - D_analytical|",
            "Grid Spacing vs Relative Error (%)",
            "Grid Spacing vs Execution Time (ms)"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )

    # 1. h vs Centre Dose
    fig.add_trace(go.Scatter(
        x=h_vals, y=fdm_doses, mode="lines+markers",
        marker=dict(size=8, color="#1e3a8a"),
        name="FDM Centre Dose",
        hovertemplate="h: %{x}<br>FDM: %{y:.6f}<extra></extra>"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=h_vals, y=fem_doses, mode="lines+markers",
        marker=dict(size=8, color="#059669", symbol="diamond"),
        name="FEM Centre Dose",
        hovertemplate="h: %{x}<br>FEM: %{y:.6f}<extra></extra>"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=h_vals, y=ref_doses, mode="lines",
        line=dict(color="#dc2626", dash="dash"),
        name="Continuous Analytical Reference",
        hovertemplate="Analytical Ref: %{y:.6f}<extra></extra>"
    ), row=1, col=1)

    # 2. h vs Absolute Error
    fig.add_trace(go.Scatter(
        x=h_vals, y=fdm_abs, mode="lines+markers",
        marker=dict(size=8, color="#1e3a8a"),
        name="FDM Error",
        showlegend=False,
        hovertemplate="h: %{x}<br>FDM Error: %{y:.6e}<extra></extra>"
    ), row=1, col=2)

    fig.add_trace(go.Scatter(
        x=h_vals, y=fem_abs, mode="lines+markers",
        marker=dict(size=8, color="#059669", symbol="diamond"),
        name="FEM Error",
        showlegend=False,
        hovertemplate="h: %{x}<br>FEM Error: %{y:.6e}<extra></extra>"
    ), row=1, col=2)

    # 3. h vs Relative Error
    fig.add_trace(go.Scatter(
        x=h_vals, y=fdm_rel, mode="lines+markers",
        marker=dict(size=8, color="#1e3a8a"),
        name="FDM Rel %",
        showlegend=False,
        hovertemplate="h: %{x}<br>FDM: %{y:.4f}%<extra></extra>"
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=h_vals, y=fem_rel, mode="lines+markers",
        marker=dict(size=8, color="#059669", symbol="diamond"),
        name="FEM Rel %",
        showlegend=False,
        hovertemplate="h: %{x}<br>FEM: %{y:.4f}%<extra></extra>"
    ), row=2, col=1)

    # 4. h vs Execution Time
    fig.add_trace(go.Scatter(
        x=h_vals, y=fdm_time, mode="lines+markers",
        marker=dict(size=8, color="#1e3a8a"),
        name="FDM Time (ms)",
        showlegend=False,
        hovertemplate="h: %{x}<br>FDM: %{y:.3f} ms<extra></extra>"
    ), row=2, col=2)

    fig.add_trace(go.Scatter(
        x=h_vals, y=fem_time, mode="lines+markers",
        marker=dict(size=8, color="#059669", symbol="diamond"),
        name="FEM Time (ms)",
        showlegend=False,
        hovertemplate="h: %{x}<br>FEM: %{y:.3f} ms<extra></extra>"
    ), row=2, col=2)

    fig.update_xaxes(title_text="Grid Spacing h", row=1, col=1)
    fig.update_xaxes(title_text="Grid Spacing h", row=1, col=2)
    fig.update_xaxes(title_text="Grid Spacing h", row=2, col=1)
    fig.update_xaxes(title_text="Grid Spacing h", row=2, col=2)

    fig.update_yaxes(title_text="Centre Dose D", row=1, col=1)
    fig.update_yaxes(title_text="|Absolute Error|", row=1, col=2)
    fig.update_yaxes(title_text="Relative Error (%)", row=2, col=1)
    fig.update_yaxes(title_text="Time (ms)", row=2, col=2)

    fig.update_layout(
        template="plotly_white",
        height=640,
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="center", x=0.5),
        margin=dict(l=50, r=40, t=70, b=50)
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
