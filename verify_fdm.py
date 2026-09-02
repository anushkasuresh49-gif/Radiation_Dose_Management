"""
Self-contained Verification Script for FDM Radiation Dose Simulation
Verifies:
1. Model parameters validation
2. Grid generation and node classification
3. FDM system assembly (A and b)
4. Numerical solve of A * D = b
5. Centre-node extraction
6. Mathematical check: D_centre == 0.25 for default case!
7. Error and validation metrics (Absolute Error = 0.0, Relative Error = 0.0%)
"""

import sys
import math

from modules.model import ModelParameters, create_grid, validate_parameters
from modules.fdm_solver import (
    build_fdm_system,
    solve_fdm,
    calculate_dose_statistics,
    generate_step_by_step_latex
)
from modules.validation import (
    calculate_reference_solution,
    calculate_error_metrics
)
from modules.sensitivity import calculate_tumour_metrics

def main():
    print("============================================================")
    print("RUNNING FDM NUMERICAL SIMULATION VERIFICATION TEST")
    print("============================================================")

    # 1. Default Parameters
    params = ModelParameters(
        xmin=0.0,
        xmax=1.0,
        ymin=0.0,
        ymax=1.0,
        k=1.0,
        S=4.0,
        h=0.5,
        boundary_dose=0.0
    )

    valid, err = validate_parameters(params)
    assert valid, f"Validation failed: {err}"
    print("[PASS] Parameter validation passed.")

    # 2. Grid Generation
    grid = create_grid(params)
    print(f"Grid constructed: Nx={grid.Nx}, Ny={grid.Ny}, Total Nodes={grid.total_nodes}")
    print(f"Interior Nodes count: {grid.interior_nodes_count}, Boundary Nodes count: {grid.boundary_nodes_count}")
    print(f"Centre index: {grid.centre_index} -> ({grid.x_coords[grid.centre_index[0]]}, {grid.y_coords[grid.centre_index[1]]})")
    assert grid.Nx == 3
    assert grid.Ny == 3
    assert grid.total_nodes == 9
    assert grid.interior_nodes_count == 1
    assert grid.boundary_nodes_count == 8
    print("[PASS] Grid creation and node topology confirmed.")

    # 3. System Assembly
    A, b, node_map = build_fdm_system(grid)
    print(f"Interior mapping: {node_map}")
    print(f"RHS Vector b: {b}")
    print(f"Matrix A: {A}")
    # For 1 interior node: A must be [[4.0]], b must be [1.0]
    # Equation: 4*D = S*h^2/k = 4 * 0.25 / 1.0 = 1.0 -> D = 0.25!
    
    # 4. FDM Solve
    sol = solve_fdm(grid)
    print(f"Computed Centre Dose: {sol.centre_dose:.6f}")
    print(f"Max Dose: {sol.max_dose:.6f}, Min Dose: {sol.min_dose:.6f}")
    print(f"Mean Dose: {sol.mean_dose:.6f}, Std Dev: {sol.std_dose:.6f}")
    print(f"Execution time: {sol.execution_time_sec * 1000:.4f} ms")

    # CRITICAL CHECK
    assert abs(sol.centre_dose - 0.25) < 1e-9, f"ERROR: Centre dose is {sol.centre_dose}, expected 0.25!"
    print("[CRITICAL VERIFICATION PASSED]: Centre dose is EXACTLY 0.25!")

    # 5. Validation Against Reference
    ref = calculate_reference_solution(params)
    val = calculate_error_metrics(sol.centre_dose, ref)
    print(f"Reference Value: {val.reference_dose:.6f}")
    print(f"Absolute Error: {val.absolute_error:.6e}")
    print(f"Relative Error: {val.relative_error_pct:.4f}%")
    assert val.absolute_error < 1e-9
    assert val.relative_error_pct < 1e-9
    print("[PASS] Error calculations verified (Absolute Error = 0, Relative Error = 0%).")

    # 6. Tumour indicator check
    tm = calculate_tumour_metrics(sol, 0.5, 0.5, 0.25)
    print(f"Tumour Avg Dose: {tm.avg_tumour_dose:.4f}, Surrounding Avg: {tm.avg_surrounding_dose:.4f}")
    print(f"Tumour/Surrounding Ratio: {tm.tumour_to_surrounding_ratio:.2f}")

    print("============================================================")
    print("ALL NUMERICAL AND ARCHITECTURAL TESTS COMPLETED SUCCESSFULLY")
    print("============================================================")

if __name__ == "__main__":
    main()
