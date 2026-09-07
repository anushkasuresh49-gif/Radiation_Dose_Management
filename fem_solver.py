"""
fem_solver.py - Root wrapper for FEM Solver Module
Re-exports from modules.fem_solver for direct script execution and testing.
"""

from modules.fem_solver import (
    FEMElement,
    FEMMesh,
    FEMSolution,
    generate_triangular_mesh,
    compute_element_stiffness,
    compute_element_load,
    assemble_global_fem_system,
    solve_fem
)

__all__ = [
    "FEMElement",
    "FEMMesh",
    "FEMSolution",
    "generate_triangular_mesh",
    "compute_element_stiffness",
    "compute_element_load",
    "assemble_global_fem_system",
    "solve_fem"
]
