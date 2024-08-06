"""
Authors:
- Yingqi Jia (yingqij2@illinois.edu)
- Chao Wang (chaow4@illinois.edu)
- Xiaojia Shelly Zhang (zhangxs@illinois.edu)

Sponsors:
- U.S. National Science Foundation (NSF) EAGER Award CMMI-2127134
- U.S. Defense Advanced Research Projects Agency (DARPA) Young Faculty Award
  (N660012314013)
- NSF CAREER Award CMMI-2047692
- NSF Award CMMI-2245251

Reference:
- Jia, Y., Wang, C. & Zhang, X.S. FEniTop: a simple FEniCSx implementation
  for 2D and 3D topology optimization supporting parallel computing.
  Struct Multidisc Optim 67, 140 (2024).
  https://doi.org/10.1007/s00158-024-03818-7
"""

import numpy as np
import dolfinx.io
from mpi4py import MPI

from fenitop.topopt import topopt


with dolfinx.io.XDMFFile(MPI.COMM_WORLD, "meshes/shell_3d.xdmf", "r") as xdmf:
    mesh = xdmf.read_mesh(name="Grid")
if MPI.COMM_WORLD.rank == 0:
    with dolfinx.io.XDMFFile(MPI.COMM_SELF, "meshes/shell_3d.xdmf", "r") as xdmf:
        mesh_serial = xdmf.read_mesh(name="Grid")
else:
    mesh_serial = None

def on_surface(x):
    return (np.isclose(x[0]**2+x[1]**2+x[2]**2, 50**2)
            & np.greater(x[2], -2) & np.less(x[2], 2))

traction_bcs = [
    [(0, 0.1, 0), lambda x: on_surface(x) & np.greater(x[0], 49.8)],
    [(-0.1, 0, 0), lambda x: on_surface(x) & np.greater(x[1], 49.8)],
    [(0, -0.1, 0), lambda x: on_surface(x) & np.less(x[0], -49.8)],
    [(0.1, 0, 0), lambda x: on_surface(x) & np.less(x[1], -49.8)],
]

fem = {  # FEA parameters
    "mesh": mesh,
    "mesh_serial": mesh_serial,
    "young's modulus": 100,
    "poisson's ratio": 0.25,
    "disp_bc": lambda x: np.less(x[2], -49) | np.greater(x[2], 49),
    "traction_bcs": traction_bcs,
    "body_force": (0, 0, 0),
    "quadrature_degree": 2,
    "petsc_options": {
        "ksp_type": "preonly",
        "pc_type": "lu",
        "pc_factor_mat_solver_type": "mumps",
    },
}

opt = {  # Topology optimization parameters
    "max_iter": 400,
    "opt_tol": 1e-5,
    "vol_frac": 0.12,
    "solid_zone": lambda x: np.full(x.shape[1], False),
    "void_zone": lambda x: np.full(x.shape[1], False),
    "penalty": 3.0,
    "epsilon": 1e-6,
    "filter_radius": 3.5,
    "beta_interval": 50,
    "beta_max": 128,
    "use_oc": True,
    "move": 0.02,
    "opt_compliance": True,
}

if __name__ == "__main__":
    topopt(fem, opt)

# Execute the code in parallel:
# mpirun -n 8 python3 scripts/shell_3d.py
