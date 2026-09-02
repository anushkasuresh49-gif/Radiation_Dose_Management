"""
Radiation Dose Distribution Optimization in Cancer Treatment
Using Finite Difference Method with Analytical Solution for Reduced Healthy Tissue Exposure
Streamlit Web Application for Academic Capstone Project
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import io

from modules.model import ModelParameters, ComputationalGrid, create_grid, validate_parameters
from modules.fdm_solver import (
    FDMSolution,
    solve_fdm,
    generate_step_by_step_latex
)
from modules.validation import (
    ValidationResult,
    calculate_reference_solution,
    calculate_error_metrics,
    create_validation_dataframe
)
from modules.convergence import (
    ConvergenceDataPoint,
    run_convergence_analysis,
    convergence_to_dataframe
)
from modules.sensitivity import (
    SensitivityResult,
    TumourExposureMetrics,
    run_sensitivity_analysis,
    calculate_tumour_metrics
)
from modules.visualization import (
    create_grid_plot,
    create_heatmap,
    create_contour_plot,
    create_3d_surface,
    create_convergence_plots,
    create_sensitivity_plots
)
from modules.report import (
    generate_summary_dataframe,
    generate_csv_report,
    generate_pdf_report,
    generate_academic_interpretation,
    HAS_REPORTLAB
)

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Radiation Dose FDM Optimization",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# CUSTOM STYLING (RESEARCH DASHBOARD AESTHETIC)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main container styling */
    .main-title {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    .main-subtitle {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .disclaimer-box {
        background-color: #fff1f2;
        border-left: 4px solid #e11d48;
        padding: 0.85rem 1.1rem;
        border-radius: 4px;
        color: #9f1239;
        font-size: 0.88rem;
        font-weight: 500;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .metric-title {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 0.4rem;
        font-weight: 600;
    }
    .metric-val {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #0284c7;
        margin-top: 0.3rem;
    }
    .module-badge {
        display: inline-block;
        background-color: #e0f2fe;
        color: #0369a1;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION (DEFAULT TEST CASE)
# -----------------------------------------------------------------------------
def initialize_state():
    if "params" not in st.session_state:
        st.session_state.params = ModelParameters(
            xmin=0.0,
            xmax=1.0,
            ymin=0.0,
            ymax=1.0,
            k=1.0,
            S=4.0,
            h=0.5,
            boundary_dose=0.0
        )
    if "tumour_params" not in st.session_state:
        st.session_state.tumour_params = {
            "cx": 0.5,
            "cy": 0.5,
            "radius": 0.25
        }
    if "solution" not in st.session_state:
        # Run default simulation immediately so 0.25 is calculated
        grid = create_grid(st.session_state.params)
        sol = solve_fdm(grid)
        ref = calculate_reference_solution(st.session_state.params)
        val = calculate_error_metrics(sol.centre_dose, ref)
        st.session_state.grid = grid
        st.session_state.solution = sol
        st.session_state.validation = val
        st.session_state.convergence = None
        st.session_state.sensitivity = None
        st.session_state.tumour_metrics = calculate_tumour_metrics(
            sol,
            st.session_state.tumour_params["cx"],
            st.session_state.tumour_params["cy"],
            st.session_state.tumour_params["radius"]
        )

initialize_state()

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### RADIATION DOSE\n## OPTIMIZATION")
    st.caption("FDM + ANALYTICAL VALIDATION")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "🏠 Project Overview",
            "📐 Module 1: Mathematical Modelling",
            "🔢 Module 2: FDM Numerical Solution",
            "📊 Module 3: Analytical Validation",
            "📈 Convergence Analysis",
            "⚙ Parameter Sensitivity",
            "📄 Results & Report"
        ]
    )

    st.markdown("---")
    st.markdown("#### Simulation Controls")

    with st.expander("Parameters Configuration", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            p_xmin = st.number_input("X min", value=st.session_state.params.xmin, step=0.1)
            p_ymin = st.number_input("Y min", value=st.session_state.params.ymin, step=0.1)
            p_k = st.number_input("Diffusion k", value=st.session_state.params.k, min_value=0.01, step=0.1)
            p_h = st.selectbox("Grid spacing h", options=[0.5, 0.25, 0.2, 0.1, 0.05], index=0)
        with c2:
            p_xmax = st.number_input("X max", value=st.session_state.params.xmax, step=0.1)
            p_ymax = st.number_input("Y max", value=st.session_state.params.ymax, step=0.1)
            p_S = st.number_input("Source S", value=st.session_state.params.S, step=1.0)
            p_bc = st.number_input("Boundary D", value=st.session_state.params.boundary_dose, step=0.1)

    if st.button("▶ Run FDM Simulation", type="primary", use_container_width=True):
        new_params = ModelParameters(
            xmin=float(p_xmin),
            xmax=float(p_xmax),
            ymin=float(p_ymin),
            ymax=float(p_ymax),
            k=float(p_k),
            S=float(p_S),
            h=float(p_h),
            boundary_dose=float(p_bc)
        )
        valid, err_msg = validate_parameters(new_params)
        if not valid:
            st.error(f"Input Error: {err_msg}")
        else:
            try:
                st.session_state.params = new_params
                grid = create_grid(new_params)
                sol = solve_fdm(grid)
                ref = calculate_reference_solution(new_params)
                val = calculate_error_metrics(sol.centre_dose, ref)

                st.session_state.grid = grid
                st.session_state.solution = sol
                st.session_state.validation = val
                st.session_state.tumour_metrics = calculate_tumour_metrics(
                    sol,
                    st.session_state.tumour_params["cx"],
                    st.session_state.tumour_params["cy"],
                    st.session_state.tumour_params["radius"]
                )
                st.success("Simulation completed successfully.")
            except Exception as ex:
                st.error(f"Solver Error: {str(ex)}")

    st.markdown("---")
    st.caption("Academic Simulation Only. Not for medical diagnosis or clinical treatment planning.")

# -----------------------------------------------------------------------------
# GLOBAL MANDATORY DISCLAIMER
# -----------------------------------------------------------------------------
st.markdown("""
<div class="disclaimer-box">
    <strong>Academic Simulation Only</strong> — This application is intended for mathematical and 
    numerical-method demonstration and must not be used for clinical diagnosis, treatment planning, 
    or medical decision-making.
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PAGE 1: PROJECT OVERVIEW
# -----------------------------------------------------------------------------
if page == "🏠 Project Overview":
    st.markdown('<div class="main-title">Radiation Dose Distribution Optimization</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Finite Difference Numerical Modelling with Analytical Validation</div>', unsafe_allow_html=True)

    st.markdown("""
    This research platform formulates and solves the steady-state radiation diffusion boundary value problem
    for cancer therapy dose distribution. By discretizing the governing elliptic Poisson PDE using the 
    Finite Difference Method (FDM), the tool computes spatial radiation absorption, verifies numerical 
    accuracy against exact analytical benchmarks, and evaluates healthy tissue sparing metrics.
    """)

    # 3 Primary Module Cards
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("""
        <div class="metric-card" style="text-align: left; height: 100%;">
            <div class="module-badge">Module 1</div>
            <h4 style="margin: 0.2rem 0 0.5rem 0; color: #0f172a;">Mathematical Modelling</h4>
            <p style="font-size: 0.85rem; color: #475569;">
                Defines the governing partial differential equation, spatial domain parameters, 
                and structured Cartesian discretization mesh.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="metric-card" style="text-align: left; height: 100%;">
            <div class="module-badge">Module 2</div>
            <h4 style="margin: 0.2rem 0 0.5rem 0; color: #0f172a;">FDM Numerical Solution</h4>
            <p style="font-size: 0.85rem; color: #475569;">
                Constructs the 5-point discrete Laplacian linear system A·D = b, solves for unknown 
                interior nodes, and maps full 2D/3D dose topology.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown("""
        <div class="metric-card" style="text-align: left; height: 100%;">
            <div class="module-badge">Module 3</div>
            <h4 style="margin: 0.2rem 0 0.5rem 0; color: #0f172a;">Analytical Validation</h4>
            <p style="font-size: 0.85rem; color: #475569;">
                Validates the numerical solution against benchmark reference solutions, evaluates 
                convergence order, and measures runtime efficiency.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Computational Simulation Workflow")
    st.markdown("""
    ```
    Problem Definition
          ↓
    Mathematical Model (-k∇²D = S)
          ↓
    Computational Domain ([0, Lx] × [0, Ly])
          ↓
    Grid Generation (Cartesian mesh with spacing h)
          ↓
    FDM Discretization (5-point central difference)
          ↓
    Linear System Assembly (A D = b)
          ↓
    Numerical Solution (Sparse linear solver)
          ↓
    Analytical Validation (|D_FDM - D_ref|)
          ↓
    Error & Convergence Analysis
          ↓
    Performance & Sensitivity Evaluation
          ↓
    Interactive Dose Visualization (2D/3D)
    ```
    """)

# -----------------------------------------------------------------------------
# PAGE 2: MODULE 1 – MATHEMATICAL MODELLING
# -----------------------------------------------------------------------------
elif page == "📐 Module 1: Mathematical Modelling":
    st.markdown("## Module 1 – Mathematical Modelling")
    st.caption("Mathematical formulation, domain configuration, and computational mesh construction.")

    # Section 1: Model Parameters
    st.markdown("### Section 1: Model Parameters")
    p = st.session_state.params
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("X Range", f"[{p.xmin}, {p.xmax}]", f"Lx = {p.Lx}")
        st.metric("Y Range", f"[{p.ymin}, {p.ymax}]", f"Ly = {p.Ly}")
    with c2:
        st.metric("Diffusion Coeff. (k)", f"{p.k}")
        st.metric("Source Intensity (S)", f"{p.S}")
    with c3:
        st.metric("Grid Spacing (h)", f"{p.h}")
        st.metric("Boundary Dose", f"{p.boundary_dose}")
    with c4:
        st.metric("Discrete Step h²", f"{p.h**2:.4f}")
        st.metric("Source Ratio S/k", f"{p.S / p.k:.2f}")

    # Section 2: Governing Equation
    st.markdown("### Section 2: Governing Equation")
    st.latex(r"-k \left( \frac{\partial^2 D}{\partial x^2} + \frac{\partial^2 D}{\partial y^2} \right) = S")
    st.markdown("""
    **Physical & Mathematical Variable Definitions:**
    - **$D(x, y)$**: Spatial radiation dose distribution within the irradiated tissue domain.
    - **$k$**: Tissue diffusion coefficient governing the spatial rate of dose dispersion.
    - **$S$**: Constant volumetric radiation source intensity emitted into the domain.
    - **$x, y$**: Two-dimensional Cartesian spatial coordinates ($0 \le x \le L_x$, $0 \le y \le L_y$).
    - **$\nabla^2 D$**: Two-dimensional Laplace operator representing spatial curvature of dose.
    """)

    # Section 3: Computational Domain
    st.markdown("### Section 3: Computational Domain & Mesh Metrics")
    grid = st.session_state.grid
    d1, d2, d3, d4, d5 = st.columns(5)
    with d1:
        st.metric("Grid Points Nx", f"{grid.Nx}")
    with d2:
        st.metric("Grid Points Ny", f"{grid.Ny}")
    with d3:
        st.metric("Total Grid Points", f"{grid.total_nodes}")
    with d4:
        st.metric("Interior Nodes", f"{grid.interior_nodes_count}")
    with d5:
        st.metric("Boundary Nodes", f"{grid.boundary_nodes_count}")

    # Section 4: Grid Visualization
    st.markdown("### Section 4: Structured Grid Visualization")
    fig_grid = create_grid_plot(grid)
    st.plotly_chart(fig_grid, use_container_width=True)

    # Section 5: Boundary Conditions
    st.markdown("### Section 5: Boundary Conditions")
    st.markdown(f"""
    Uniform Dirichlet boundary conditions are imposed along the outer borders of the computational domain:
    - **$D(x_{\\min}, y) = {p.boundary_dose}$** (Left Boundary, $x = {p.xmin}$)
    - **$D(x_{\\max}, y) = {p.boundary_dose}$** (Right Boundary, $x = {p.xmax}$)
    - **$D(x, y_{\\min}) = {p.boundary_dose}$** (Bottom Boundary, $y = {p.ymin}$)
    - **$D(x, y_{\\max}) = {p.boundary_dose}$** (Top Boundary, $y = {p.ymax}$)
    """)

    # Section 6: Model Summary
    st.markdown("### Section 6: Model Summary")
    st.markdown(f"""
    | Parameter | Configured Value | Description |
    | :--- | :--- | :--- |
    | **Domain Bounds** | $[{p.xmin}, {p.xmax}] \\times [{p.ymin}, {p.ymax}]$ | Spatial extent ($L_x={p.Lx}, L_y={p.Ly}$) |
    | **Grid Spacing ($h$)** | ${p.h}$ | Mesh resolution along $x$ and $y$ |
    | **Diffusion Coeff. ($k$)** | ${p.k}$ | Governing transport rate |
    | **Source Term ($S$)** | ${p.S}$ | Internal radiation generation |
    | **Boundary Dose ($D_b$)** | ${p.boundary_dose}$ | Dirichlet perimeter condition |
    | **Total Grid Points** | ${grid.total_nodes}$ | $N_x \\times N_y = {grid.Nx} \\times {grid.Ny}$ |
    | **Interior Unknowns** | ${grid.interior_nodes_count}$ | Linear system matrix size ($N_{{int}} \\times N_{{int}}$) |
    """)

# -----------------------------------------------------------------------------
# PAGE 3: MODULE 2 – FDM NUMERICAL SOLUTION
# -----------------------------------------------------------------------------
elif page == "🔢 Module 2: FDM Numerical Solution":
    st.markdown("## Module 2 – FDM Numerical Solution")
    st.caption("Finite Difference discretization, linear system assembly, and full spatial dose field computation.")

    sol = st.session_state.solution
    p = st.session_state.params

    # Discretization formulation
    st.markdown("### FDM Central Discretization Formulation")
    st.latex(r"\frac{\partial^2 D}{\partial x^2} \approx \frac{D_{i+1,j} - 2D_{i,j} + D_{i-1,j}}{h^2}, \quad \frac{\partial^2 D}{\partial y^2} \approx \frac{D_{i,j+1} - 2D_{i,j} + D_{i,j-1}}{h^2}")
    st.latex(r"-\left[ \frac{D_{i+1,j} - 2D_{i,j} + D_{i-1,j}}{h^2} + \frac{D_{i,j+1} - 2D_{i,j} + D_{i,j-1}}{h^2} \right] = \frac{S}{k}")
    st.markdown("**Equivalent 5-point discrete stencil linear formulation:**")
    st.latex(r"4D_{i,j} - D_{i+1,j} - D_{i-1,j} - D_{i,j+1} - D_{i,j-1} = \frac{S h^2}{k}")

    # Expandable: Step-by-step mathematical calculation
    with st.expander("Show Detailed FDM Calculation", expanded=True):
        st.markdown("#### Analytical Step-by-Step System Derivation")
        latex_code = generate_step_by_step_latex(p, sol.centre_dose)
        st.latex(latex_code)
        st.info(f"Dynamically verified from numerical solver: Calculated Centre Dose = **{sol.centre_dose:.6f}**.")

    # Results Metrics Cards
    st.markdown("### Numerical Results & Statistics")
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1:
        st.metric("Centre-Point Dose", f"{sol.centre_dose:.6f}")
        st.metric("Matrix Dimension", f"{sol.matrix_dim} × {sol.matrix_dim}")
    with r2:
        st.metric("Maximum Dose", f"{sol.max_dose:.6f}")
        st.metric("Minimum Dose", f"{sol.min_dose:.6f}")
    with r3:
        st.metric("Mean Dose", f"{sol.mean_dose:.6f}")
        st.metric("Median Dose", f"{sol.median_dose:.6f}")
    with r4:
        st.metric("Standard Deviation", f"{sol.std_dose:.6f}")
        st.metric("Execution Time", f"{sol.execution_time_sec * 1000:.3f} ms")
    with r5:
        st.metric("Total Grid Points", f"{sol.grid.total_nodes}")
        st.metric("Interior Nodes", f"{sol.grid.interior_nodes_count}")

    # 3 Visualizations in Tabs
    st.markdown("### Spatial Dose Field Visualizations")
    tab_heat, tab_contour, tab_3d = st.tabs(["2D Dose Heatmap", "Isodose Contour Plot", "3D Surface Elevation"])

    with tab_heat:
        fig_heat = create_heatmap(sol)
        st.plotly_chart(fig_heat, use_container_width=True)
    with tab_contour:
        fig_cont = create_contour_plot(sol)
        st.plotly_chart(fig_cont, use_container_width=True)
    with tab_3d:
        fig_3d = create_3d_surface(sol)
        st.plotly_chart(fig_3d, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 4: MODULE 3 – ANALYTICAL VALIDATION
# -----------------------------------------------------------------------------
elif page == "📊 Module 3: Analytical Validation":
    st.markdown("## Module 3 – Analytical Validation & Performance Evaluation")
    st.caption("Quantitative benchmark comparison against analytical reference solution.")

    sol = st.session_state.solution
    val = st.session_state.validation

    # Metric Cards
    v1, v2, v3, v4 = st.columns(4)
    with v1:
        st.metric("FDM Centre Dose", f"{val.fdm_centre_dose:.6f}")
    with v2:
        st.metric("Analytical/Reference Dose", f"{val.reference_dose:.6f}")
    with v3:
        st.metric("Absolute Error", f"{val.absolute_error:.6e}" if val.absolute_error < 1e-4 else f"{val.absolute_error:.6f}")
    with v4:
        st.metric("Relative Error (%)", f"{val.relative_error_pct:.4f}%")

    st.markdown("### Benchmark Validation Table")
    val_df = create_validation_dataframe(val)
    st.table(val_df)

    st.markdown("""
    **Validation Notes:**
    - For the default reference demonstration case ($L_x=1, L_y=1, k=1, S=4, h=0.5, D_b=0$), the exact discrete balance 
      at the single interior centre node yields $16 D = 4 \implies D = 0.25$.
    - The FDM solver programmatically yields an absolute error of **0.00** and a relative error of **0.00%**, 
      confirming the mathematical correctness and algebraic integrity of the matrix assembly algorithm.
    """)

    # Performance Evaluation Summary
    st.markdown("### Computational Performance Evaluation")
    perf_data = [
        {"Metric": "Measured Solver Runtime", "Value": f"{sol.execution_time_sec * 1000:.3f} ms (using time.perf_counter())"},
        {"Metric": "Linear System Matrix Dimensions", "Value": f"{sol.matrix_dim} × {sol.matrix_dim}"},
        {"Metric": "Total Spatial Degrees of Freedom", "Value": f"{sol.grid.total_nodes} nodes"},
        {"Metric": "Interior Unknowns Discretized", "Value": f"{sol.grid.interior_nodes_count}"},
        {"Metric": "Linear Solver Methodology", "Value": "SciPy Sparse Direct LU / Gaussian Elimination"}
    ]
    st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# PAGE 5: CONVERGENCE ANALYSIS
# -----------------------------------------------------------------------------
elif page == "📈 Convergence Analysis":
    st.markdown("## Grid Convergence Analysis")
    st.caption("Evaluation of numerical solution consistency and execution performance across multi-scale mesh refinement.")

    p = st.session_state.params
    st.markdown("Select grid spacing options to run systematic mesh refinement:")

    selected_spacings = st.multiselect(
        "Candidate Grid Spacings (h)",
        options=[0.5, 0.25, 0.2, 0.1, 0.05],
        default=[0.5, 0.25, 0.2, 0.1]
    )

    if st.button("Run Convergence Sweep", type="primary"):
        if not selected_spacings:
            st.warning("Please select at least one grid spacing.")
        else:
            with st.spinner("Running FDM solver across refinement levels..."):
                conv_data = run_convergence_analysis(p, selected_spacings)
                st.session_state.convergence = conv_data

    if st.session_state.convergence:
        conv_df = convergence_to_dataframe(st.session_state.convergence)
        st.markdown("### Convergence Data Table")
        st.dataframe(conv_df, use_container_width=True, hide_index=True)

        st.markdown("### Interactive Convergence Curves")
        fig_conv = create_convergence_plots(st.session_state.convergence)
        st.plotly_chart(fig_conv, use_container_width=True)
    else:
        st.info("Click 'Run Convergence Sweep' to compute error curves across the selected mesh resolutions.")

# -----------------------------------------------------------------------------
# PAGE 6: PARAMETER SENSITIVITY & REDUCED HEALTHY TISSUE EXPOSURE
# -----------------------------------------------------------------------------
elif page == "⚙ Parameter Sensitivity":
    st.markdown("## Parameter Sensitivity & Tissue Exposure")
    st.caption("Physical parameter sensitivity sweeps and academic tissue exposure indicators.")

    p = st.session_state.params

    # 1. Parameter Sensitivity Sweep
    st.markdown("### Parameter Sensitivity Analysis")
    if st.button("Run Sensitivity Sweep", type="primary"):
        with st.spinner("Executing parameter variations through FDM solver..."):
            sens_res = run_sensitivity_analysis(p)
            st.session_state.sensitivity = sens_res

    if st.session_state.sensitivity:
        fig_sens = create_sensitivity_plots(st.session_state.sensitivity)
        st.plotly_chart(fig_sens, use_container_width=True)

        st.markdown("**Automated Academic Interpretation:**")
        st.info(st.session_state.sensitivity.interpretation)
    else:
        st.info("Click 'Run Sensitivity Sweep' to analyze parameter responses for k, S, and h.")

    st.markdown("---")

    # 2. Reduced Healthy Tissue Exposure Indicators
    st.markdown("### Reduced Healthy Tissue Exposure (Simulation Indicators)")
    st.caption("Academic mathematical spatial region-of-interest analysis.")

    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        t_cx = st.number_input("Tumour Centre X", value=st.session_state.tumour_params["cx"], min_value=p.xmin, max_value=p.xmax, step=0.05)
    with tc2:
        t_cy = st.number_input("Tumour Centre Y", value=st.session_state.tumour_params["cy"], min_value=p.ymin, max_value=p.ymax, step=0.05)
    with tc3:
        t_rad = st.number_input("Tumour Radius", value=st.session_state.tumour_params["radius"], min_value=0.05, max_value=0.5, step=0.05)

    if st.button("Update Exposure Indicators"):
        st.session_state.tumour_params = {"cx": t_cx, "cy": t_cy, "radius": t_rad}
        st.session_state.tumour_metrics = calculate_tumour_metrics(
            st.session_state.solution, t_cx, t_cy, t_rad
        )
        st.success("Tissue exposure indicators updated.")

    tm = st.session_state.tumour_metrics
    e1, e2, e3, e4, e5 = st.columns(5)
    with e1:
        st.metric("Avg Tumour Dose", f"{tm.avg_tumour_dose:.4f}")
    with e2:
        st.metric("Max Tumour Dose", f"{tm.max_tumour_dose:.4f}")
    with e3:
        st.metric("Avg Healthy Surrounding", f"{tm.avg_surrounding_dose:.4f}")
    with e4:
        st.metric("Max Healthy Surrounding", f"{tm.max_surrounding_dose:.4f}")
    with e5:
        st.metric("Tumour / Surrounding Ratio", f"{tm.tumour_to_surrounding_ratio:.2f}x")

    st.markdown("""
    <div class="disclaimer-box" style="margin-top: 1rem;">
        <strong>Simulation-based dose exposure indicators:</strong> Values reflect mathematical integrations 
        over the defined geometry. These metrics must not be interpreted as safe clinical doses, recommended 
        treatment doses, or clinically acceptable limits.
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PAGE 7: RESULTS & REPORT
# -----------------------------------------------------------------------------
elif page == "📄 Results & Report":
    st.markdown("## Results & Formal Research Report")
    st.caption("Comprehensive numerical synthesis, data exports, and downloadable academic reports.")

    sol = st.session_state.solution
    val = st.session_state.validation
    tumour = st.session_state.tumour_metrics
    p = st.session_state.params

    # Summary table
    st.markdown("### Executive Simulation Summary")
    sum_df = generate_summary_dataframe(sol, val)
    st.dataframe(sum_df, use_container_width=True, hide_index=True)

    # Academic Interpretation
    st.markdown("### Academic Interpretation")
    interp_text = generate_academic_interpretation(sol, val, tumour)
    st.info(interp_text)

    # Downloads
    st.markdown("### Export Research Reports")
    d_col1, d_col2 = st.columns(2)

    with d_col1:
        csv_data = generate_csv_report(sol, val)
        st.download_button(
            label="📥 Download Numerical Dataset (CSV)",
            data=csv_data,
            file_name="radiation_dose_fdm_results.csv",
            mime="text/csv",
            use_container_width=True
        )

    with d_col2:
        if HAS_REPORTLAB:
            try:
                pdf_bytes = generate_pdf_report(sol, val, st.session_state.convergence, tumour)
                st.download_button(
                    label="📄 Download Academic Research Report (PDF)",
                    data=pdf_bytes,
                    file_name="radiation_dose_fdm_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"PDF generation encountered an issue: {e}")
        else:
            st.info("ReportLab is not installed; PDF export requires `pip install reportlab`.")
