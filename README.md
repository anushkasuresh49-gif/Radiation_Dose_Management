# Optimizing Radiation Dose Distribution in Cancer Treatment Using Finite Difference Method with Analytical Solution for Reduced Healthy Tissue Exposure

## Academic Capstone Project

**Academic Simulation Only** — This application is intended for mathematical and numerical-method demonstration and must not be used for clinical diagnosis, treatment planning, or medical decision-making.

---

## 1. Project Overview & Description

This software platform provides an interactive academic simulation for modeling, computing, and optimizing radiation dose distribution across biological tissue domains. By formulating the steady-state radiation transport problem as an elliptic partial differential equation (Poisson-type diffusion PDE), the application discretizes the continuous domain using the **Finite Difference Method (FDM)** on a structured Cartesian mesh.

The resulting discrete system of algebraic equations is solved using sparse linear algebra routines. The application validates computed numerical results against benchmark analytical reference solutions, performs mesh refinement convergence studies, carries out parameter sensitivity sweeps, and computes spatial indicators to assess reduced exposure to surrounding healthy tissue.

---

## 2. Primary Objectives

1. **Mathematical Modelling**: Formulate the boundary-value problem for spatial radiation dose dispersion.
2. **Domain & Discretization**: Discretize the domain $[0, L_x] \times [0, L_y]$ into uniform grid cells of spacing $h$.
3. **Discrete System Assembly**: Implement the 5-point central difference Laplacian stencil into matrix-vector form $\mathbf{A} \mathbf{D} = \mathbf{b}$.
4. **Numerical Solution**: Solve the system using direct sparse matrix factorization.
5. **Interactive Visualization**: Map dose distributions using 2D heatmaps, isodose contour maps, and 3D surface elevation models.
6. **Analytical Validation**: Compare the numerical centre-point dose against the benchmark reference solution ($D = 0.25$ for the canonical test case).
7. **Error Analysis**: Programmatically calculate absolute error $|D_{\text{FDM}} - D_{\text{ref}}|$ and percentage relative error.
8. **Grid Convergence**: Study asymptotic convergence and computational execution time as grid spacing $h \to 0$.
9. **Sensitivity Analysis**: Measure physical parameter sensitivity to diffusion coefficient $k$, source intensity $S$, and grid spacing $h$.
10. **Healthy Tissue Sparing**: Provide simulation-based spatial region-of-interest indicators for tumour and normal tissue exposure.

---

## 3. Project Modules

The application is structured into three primary modules:

- **Module 1 – Mathematical Modelling of Radiation Dose Distribution**: Domain specification, governing PDE LaTeX presentation, node classification (boundary vs. interior), and interactive mesh visualization.
- **Module 2 – Numerical Solution Using Finite Difference Method**: Assembly of coefficient matrix $\mathbf{A}$ and source/boundary vector $\mathbf{b}$, sparse linear solution, step-by-step mathematical calculation, and 2D/3D visualizations.
- **Module 3 – Analytical Validation and Performance Evaluation**: Quantitative validation against benchmark reference solution, error metrics, multi-scale grid convergence, parameter sensitivity analysis, and automated report generation.

---

## 4. Mathematical Model & FDM Discretization

### Governing Partial Differential Equation
$$-k \left( \frac{\partial^2 D}{\partial x^2} + \frac{\partial^2 D}{\partial y^2} \right) = S$$

where:
- $D(x, y)$ is the absorbed radiation dose field.
- $k$ is the diffusion transport coefficient ($k > 0$).
- $S$ is the constant internal radiation source term.
- $x, y$ are spatial coordinates over the domain $0 \le x \le L_x$, $0 \le y \le L_y$.

### Dirichlet Boundary Conditions
$$D = D_{\text{boundary}} \quad \text{on } x \in \{0, L_x\} \text{ and } y \in \{0, L_y\}$$

### 5-Point Central Finite Difference Discretization
For a uniform grid spacing $h$:
$$\frac{\partial^2 D}{\partial x^2} \approx \frac{D_{i+1,j} - 2D_{i,j} + D_{i-1,j}}{h^2}$$
$$\frac{\partial^2 D}{\partial y^2} \approx \frac{D_{i,j+1} - 2D_{i,j} + D_{i,j-1}}{h^2}$$

Substituting into the governing PDE:
$$-\left[ \frac{D_{i+1,j} - 2D_{i,j} + D_{i-1,j}}{h^2} + \frac{D_{i,j+1} - 2D_{i,j} + D_{i,j-1}}{h^2} \right] = \frac{S}{k}$$

Multiplying by $-h^2$ yields the linear algebraic stencil for each interior node $(i, j)$:
$$4 D_{i,j} - D_{i+1,j} - D_{i-1,j} - D_{i,j+1} - D_{i,j-1} = \frac{S h^2}{k}$$

### Canonical Benchmark Verification ($h = 0.5$)
For the default demonstration case:
- Domain: $L_x = 1.0, L_y = 1.0$
- Parameters: $k = 1.0, S = 4.0, h = 0.5, D_{\text{boundary}} = 0$
- Grid points: $x \in \{0, 0.5, 1.0\}$, $y \in \{0, 0.5, 1.0\}$ ($N_x = 3, N_y = 3$, 1 interior centre node)

At the centre node $(1, 1)$, all 4 adjacent neighbors are on the zero Dirichlet boundary:
$$4 D_{1,1} - 0 - 0 - 0 - 0 = \frac{4 \times (0.5)^2}{1} = 1.0 \implies D_{1,1} = \frac{1.0}{4.0} = 0.25$$

The application computes this value directly from the matrix equation without hard-coding.

---

## 5. Project Directory Structure

```
├── app.py                      # Main Streamlit Web Application Dashboard
├── modules/
│   ├── __init__.py             # Package initializer and module exports
│   ├── model.py                # Model parameters and Cartesian grid generator
│   ├── fdm_solver.py           # 5-point FDM matrix builder and sparse solver
│   ├── validation.py           # Analytical benchmark and error metrics
│   ├── convergence.py          # Grid refinement and convergence sweep
│   ├── sensitivity.py          # Parameter sweep & tumour exposure metrics
│   ├── visualization.py        # Plotly interactive 2D heatmaps, contours & 3D surfaces
│   └── report.py               # Summary tables, CSV export & PDF generator
├── verify_fdm.py               # Headless verification script for mathematical correctness
├── requirements.txt            # Python package dependencies
└── README.md                   # Academic project documentation
```

---

## 6. Installation & Execution

### Prerequisites
- Python 3.9, 3.10, or 3.11
- pip package manager

### Step 1: Clone or extract the repository
```bash
cd radiation_dose_fdm
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Verify the mathematical model (Headless Test)
```bash
python verify_fdm.py
```
Expected terminal output:
```
[CRITICAL VERIFICATION PASSED]: Centre dose is EXACTLY 0.25!
Absolute Error: 0.000000e+00
Relative Error: 0.0000%
```

### Step 4: Run the Streamlit Application
```bash
streamlit run app.py
```
Open your web browser at `http://localhost:8501`.

---

## 7. Example Inputs & Expected Outputs

| Input Parameter | Default Value | Description |
| :--- | :--- | :--- |
| **Domain X** | $[0, 1.0]$ | Spatial length $L_x = 1.0$ |
| **Domain Y** | $[0, 1.0]$ | Spatial length $L_y = 1.0$ |
| **Diffusion Coeff. ($k$)** | $1.0$ | Tissue diffusion coefficient |
| **Source Intensity ($S$)** | $4.0$ | Uniform internal radiation source |
| **Grid Spacing ($h$)** | $0.5$ | Discretization step size |
| **Boundary Dose ($D_b$)**| $0.0$ | Zero Dirichlet boundary condition |

### Expected Output
- **Centre-Point Dose**: $0.250000$
- **Analytical Benchmark Dose**: $0.250000$
- **Absolute Error**: $0.000000$
- **Relative Error**: $0.0000\%$
- **Matrix Dimension**: $1 \times 1$ interior system (expands dynamically for finer $h$)

---

## 8. Limitations

1. **Geometry**: The current implementation utilizes a structured 2D Cartesian grid. Complex patient-specific 3D anatomical contours require unstructured finite element (FEM) or boundary element (BEM) meshes.
2. **Homogeneity**: The diffusion coefficient $k$ is treated as piecewise constant or uniform within the simulated region.
3. **Steady-State Approximation**: The model solves the elliptic equilibrium equation $-k\nabla^2 D = S$, assuming time-invariant cumulative dose deposition.

---

## 9. Academic Disclaimer

**Academic Simulation Only** — This application is intended for mathematical and numerical-method demonstration and must not be used for clinical diagnosis, treatment planning, or medical decision-making. No medical advice, clinical efficacy claims, or patient safety determinations are provided by this software.
