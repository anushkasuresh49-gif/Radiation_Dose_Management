"""
Module: model.py
Mathematical Model Definition and Computational Grid Generation
Governing PDE: -k (∂²D/∂x² + ∂²D/∂y²) = S
"""

from dataclasses import dataclass
from typing import Tuple, List, Optional
import math

try:
    import numpy as np
except ImportError:
    np = None


@dataclass
class ModelParameters:
    """Class representing user parameters for radiation dose simulation."""
    xmin: float = 0.0
    xmax: float = 1.0
    ymin: float = 0.0
    ymax: float = 1.0
    k: float = 1.0            # Diffusion coefficient
    S: float = 4.0            # Radiation source intensity
    h: float = 0.5            # Grid spacing
    boundary_dose: float = 0.0 # Uniform Dirichlet boundary dose

    @property
    def Lx(self) -> float:
        return self.xmax - self.xmin

    @property
    def Ly(self) -> float:
        return self.ymax - self.ymin


@dataclass
class ComputationalGrid:
    """Class representing structured 2D computational domain grid."""
    params: ModelParameters
    x_coords: List[float]
    y_coords: List[float]
    Nx: int  # Number of grid points in x
    Ny: int  # Number of grid points in y
    total_nodes: int
    interior_nodes_count: int
    boundary_nodes_count: int
    node_types: List[List[str]]  # 'boundary', 'interior', 'centre'
    centre_index: Tuple[int, int]


def validate_parameters(params: ModelParameters) -> Tuple[bool, Optional[str]]:
    """
    Validate user input parameters.
    Checks:
    - xmax > xmin
    - ymax > ymin
    - k > 0
    - h > 0
    - domain compatibility with h
    - at least one interior node exists
    """
    if params.xmax <= params.xmin:
        return False, f"Domain length in X must be positive (xmax > xmin). Received: xmin={params.xmin}, xmax={params.xmax}."
    
    if params.ymax <= params.ymin:
        return False, f"Domain length in Y must be positive (ymax > ymin). Received: ymin={params.ymin}, ymax={params.ymax}."
    
    if params.k <= 0:
        return False, f"Diffusion coefficient k must be strictly positive (k > 0). Received: k={params.k}."
    
    if params.h <= 0:
        return False, f"Grid spacing h must be strictly positive (h > 0). Received: h={params.h}."
    
    Lx = params.Lx
    Ly = params.Ly

    # Check if grid spacing fits into domain with reasonable tolerance
    nx_float = Lx / params.h
    ny_float = Ly / params.h
    
    if abs(nx_float - round(nx_float)) > 1e-4:
        return False, f"Grid spacing h={params.h} does not divide domain length Lx={Lx:.4f} evenly (Lx/h = {nx_float:.2f}). Please choose h such that Lx/h is an integer."
    
    if abs(ny_float - round(ny_float)) > 1e-4:
        return False, f"Grid spacing h={params.h} does not divide domain length Ly={Ly:.4f} evenly (Ly/h = {ny_float:.2f}). Please choose h such that Ly/h is an integer."
    
    Nx = int(round(nx_float)) + 1
    Ny = int(round(ny_float)) + 1

    if Nx < 3 or Ny < 3:
        return False, f"Grid spacing h={params.h} is too coarse for domain ({Lx}x{Ly}). Need at least 3 points along each axis (Nx={Nx}, Ny={Ny}) to produce interior nodes."
    
    interior_nodes = (Nx - 2) * (Ny - 2)
    if interior_nodes < 1:
        return False, f"Domain and grid spacing configuration must have at least one interior node. Currently interior nodes = {interior_nodes}."
    
    return True, None


def create_grid(params: ModelParameters) -> ComputationalGrid:
    """
    Construct the structured 2D Cartesian grid based on domain and grid spacing h.
    Generates x and y coordinate lists and classifies every node as boundary, interior, or centre.
    """
    valid, err = validate_parameters(params)
    if not valid:
        raise ValueError(err)

    Nx = int(round(params.Lx / params.h)) + 1
    Ny = int(round(params.Ly / params.h)) + 1

    x_coords = [round(params.xmin + i * params.h, 6) for i in range(Nx)]
    y_coords = [round(params.ymin + j * params.h, 6) for j in range(Ny)]

    total_nodes = Nx * Ny
    interior_count = (Nx - 2) * (Ny - 2)
    boundary_count = total_nodes - interior_count

    # Identify centre node (closest to domain centroid)
    cx_ideal = (params.xmin + params.xmax) / 2.0
    cy_ideal = (params.ymin + params.ymax) / 2.0

    best_ci = 1
    best_cj = 1
    min_dist = float('inf')

    for i in range(1, Nx - 1):
        for j in range(1, Ny - 1):
            d = math.hypot(x_coords[i] - cx_ideal, y_coords[j] - cy_ideal)
            if d < min_dist:
                min_dist = d
                best_ci = i
                best_cj = j

    centre_index = (best_ci, best_cj)

    # Node type matrix: (Ny rows by Nx cols or node_types[j][i])
    node_types: List[List[str]] = []
    for j in range(Ny):
        row: List[str] = []
        for i in range(Nx):
            if i == 0 or i == Nx - 1 or j == 0 or j == Ny - 1:
                row.append("boundary")
            elif (i, j) == centre_index:
                row.append("centre")
            else:
                row.append("interior")
        node_types.append(row)

    return ComputationalGrid(
        params=params,
        x_coords=x_coords,
        y_coords=y_coords,
        Nx=Nx,
        Ny=Ny,
        total_nodes=total_nodes,
        interior_nodes_count=interior_count,
        boundary_nodes_count=boundary_count,
        node_types=node_types,
        centre_index=centre_index
    )
