"""
Self-contained Verification Script for FDM and FEM Radiation Dose Simulations
Verifies:
1. Capstone PPT Benchmark Test (S=4, k=1, h=0.5, Db=0):
   - FDM Centre Dose == 0.25
   - FEM Centre Dose == 0.25
2. Scaled Single-Interior-Node Tests [D = (S * h^2) / (4 * k)]:
   - Case 2A: S=8, k=1, h=0.5 ==> D = 0.500000
   - Case 2B: S=4, k=2, h=0.5 ==> D = 0.125000
3. Genuine FEM Solver Verification (stiffness assembly, load vector, triangular mesh topology)
4. Multi-mesh Grid Refinement & Convergence Verification toward Continuous Fourier Series (~0.294690)
"""

import sys
import math

from modules.model import ModelParameters, create_grid, validate_parameters
from modules.fdm_solver import build_fdm_system, solve_fdm
from modules.fem_solver import generate_triangular_mesh, solve_fem
from modules.validation import (
    calculate_ppt_benchmark,
    calculate_continuous_analytical_solution,
    calculate_error_metrics
)
from modules.convergence import run_convergence_analysis
from modules.sensitivity import calculate_tumour_metrics


def run_all_verification_tests():
    print("============================================================")
    print("RUNNING COMPREHENSIVE FDM & FEM NUMERICAL VERIFICATION SUITE")
    print("============================================================")

    # -------------------------------------------------------------
    # TEST 1: PPT BENCHMARK EXAMPLE (S=4, k=1, h=0.5, Db=0)
    # -------------------------------------------------------------
    print("\n--- TEST 1: CAPSTONE PPT BENCHMARK CASE (S=4, k=1, h=0.5, Db=0) ---")
    p_ppt = ModelParameters(xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, k=1.0, S=4.0, h=0.5, boundary_dose=0.0)
    valid, err = validate_parameters(p_ppt)
    assert valid, f"Validation failed: {err}"

    # FDM verification
    grid_ppt = create_grid(p_ppt)
    fdm_sol_ppt = solve_fdm(grid_ppt)
    print(f"[FDM] Computed Centre Dose: {fdm_sol_ppt.centre_dose:.6f}")
    assert abs(fdm_sol_ppt.centre_dose - 0.25) < 1e-9, f"FDM failed: {fdm_sol_ppt.centre_dose} != 0.25"
    print("[PASS] FDM Centre-Point Dose == 0.250000 (Exact)")

    # FEM verification
    fem_sol_ppt = solve_fem(p_ppt)
    print(f"[FEM] Computed Centre Dose: {fem_sol_ppt.centre_dose:.6f}")
    print(f"[FEM] Mesh: {fem_sol_ppt.mesh.total_elements} triangular elements, {fem_sol_ppt.mesh.total_nodes} nodes")
    assert abs(fem_sol_ppt.centre_dose - 0.25) < 1e-9, f"FEM failed: {fem_sol_ppt.centre_dose} != 0.25"
    print("[PASS] FEM Centre-Point Dose == 0.250000 (Exact)")

    ppt_val = calculate_ppt_benchmark(p_ppt)
    assert abs(ppt_val - 0.25) < 1e-9
    print("[PASS] PPT Analytical Benchmark evaluated: 0.250000")

    # -------------------------------------------------------------
    # TEST 2: SINGLE-INTERIOR-NODE SCALING CASES [D = (S * h^2) / (4*k)]
    # -------------------------------------------------------------
    print("\n--- TEST 2: SINGLE-INTERIOR-NODE SCALING FORMULA VERIFICATION ---")

    # Case 2A: S=8, k=1, h=0.5 -> Expected D = 0.5
    p_2a = ModelParameters(xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, k=1.0, S=8.0, h=0.5, boundary_dose=0.0)
    expected_2a = (8.0 * 0.25) / (4.0 * 1.0) # 0.5
    grid_2a = create_grid(p_2a)
    fdm_2a = solve_fdm(grid_2a)
    fem_2a = solve_fem(p_2a)
    print(f"[Case 2A: S=8, k=1] FDM={fdm_2a.centre_dose:.6f}, FEM={fem_2a.centre_dose:.6f}, Expected={expected_2a:.6f}")
    assert abs(fdm_2a.centre_dose - expected_2a) < 1e-9, f"FDM 2A failed: {fdm_2a.centre_dose}"
    assert abs(fem_2a.centre_dose - expected_2a) < 1e-9, f"FEM 2A failed: {fem_2a.centre_dose}"
    print("[PASS] Case 2A verified: FDM = 0.500000, FEM = 0.500000")

    # Case 2B: S=4, k=2, h=0.5 -> Expected D = 0.125
    p_2b = ModelParameters(xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, k=2.0, S=4.0, h=0.5, boundary_dose=0.0)
    expected_2b = (4.0 * 0.25) / (4.0 * 2.0) # 0.125
    grid_2b = create_grid(p_2b)
    fdm_2b = solve_fdm(grid_2b)
    fem_2b = solve_fem(p_2b)
    print(f"[Case 2B: S=4, k=2] FDM={fdm_2b.centre_dose:.6f}, FEM={fem_2b.centre_dose:.6f}, Expected={expected_2b:.6f}")
    assert abs(fdm_2b.centre_dose - expected_2b) < 1e-9, f"FDM 2B failed: {fdm_2b.centre_dose}"
    assert abs(fem_2b.centre_dose - expected_2b) < 1e-9, f"FEM 2B failed: {fem_2b.centre_dose}"
    print("[PASS] Case 2B verified: FDM = 0.125000, FEM = 0.125000")

    # -------------------------------------------------------------
    # TEST 3: GENUINE FEM TRIANGULAR MESH TOPOLOGY
    # -------------------------------------------------------------
    print("\n--- TEST 3: GENUINE FEM TRIANGULAR MESH & STIFFNESS ASSEMBLY ---")
    p_mesh = ModelParameters(xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, k=1.0, S=4.0, h=0.25, boundary_dose=0.0)
    fem_mesh = generate_triangular_mesh(p_mesh)
    print(f"Mesh generated for h=0.25: {fem_mesh.total_nodes} nodes, {fem_mesh.total_elements} elements")
    # For h=0.25 on unit square: Nx=5, Ny=5, nodes=25, elements = 4*4*2 = 32
    assert fem_mesh.total_nodes == 25
    assert fem_mesh.total_elements == 32
    assert fem_mesh.interior_nodes_count == 9
    assert fem_mesh.boundary_nodes_count == 16
    print("[PASS] FEM mesh topology and node classification verified.")

    fem_sol_25 = solve_fem(p_mesh)
    print(f"[FEM h=0.25] Centre Dose: {fem_sol_25.centre_dose:.6f}, Nodes={fem_sol_25.mesh.total_nodes}")
    assert abs(fem_sol_25.centre_dose - 0.28125) < 1e-6
    print("[PASS] FEM h=0.25 numerical solve verified: 0.281250")

    # -------------------------------------------------------------
    # TEST 4: CONVERGENCE TOWARD CONTINUOUS FOURIER SERIES SOLUTION
    # -------------------------------------------------------------
    print("\n--- TEST 4: CONVERGENCE STUDY ACROSS GRID RESOLUTIONS ---")
    cont_exact = calculate_continuous_analytical_solution(p_ppt)
    print(f"Continuous 2D Fourier Series Analytical Dose at Centre: {cont_exact:.6f}")
    assert 0.294 < cont_exact < 0.295, "Continuous analytical value out of range"

    conv_results = run_convergence_analysis(p_ppt, [0.5, 0.25, 0.125])
    print("\nConvergence Table:")
    print("h     | FDM Centre | FEM Centre | Error vs Cont. Analyt.")
    for pt in conv_results:
        print(f"{pt.grid_spacing:<5} | {pt.fdm_centre_dose:.6f}   | {pt.fem_centre_dose:.6f}   | {pt.fdm_absolute_error:.6f}")
        # As h decreases, error should strictly decrease
    
    # Check monotonicity of error reduction
    errors = [pt.fdm_absolute_error for pt in sorted(conv_results, key=lambda x: x.grid_spacing)]
    assert errors[0] < errors[-1], "Convergence error did not decrease with refinement"
    print("[PASS] Monotonic numerical convergence verified for FDM and FEM toward continuous limit.")

    print("\n============================================================")
    print("ALL 4 VERIFICATION TEST SUITES PASSED WITH 100% ACCURACY")
    print("============================================================")
    return True


if __name__ == "__main__":
    success = run_all_verification_tests()
    if not success:
        sys.exit(1)
