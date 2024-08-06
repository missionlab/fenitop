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
from mpi4py import MPI
from dolfinx.mesh import create_rectangle, CellType

from fenitop.topopt import topopt


def in_locator(x):
    return np.isclose(x[0], 0) & np.less(x[1], 1.5) & np.greater(x[1], -1.5)

def out_locator(x):
    return np.isclose(x[0], 10) & np.less(x[1], 1.5) & np.greater(x[1], -1.5)

mesh = create_rectangle(MPI.COMM_WORLD, [[0, -5], [10, 5]],
                        [200, 200], CellType.quadrilateral)
if MPI.COMM_WORLD.rank == 0:
    mesh_serial = create_rectangle(MPI.COMM_SELF, [[0, -5], [10, 5]],
                                   [200, 200], CellType.quadrilateral)
else:
    mesh_serial = None

fem = {  # FEA parameters
    "mesh": mesh,
    "mesh_serial": mesh_serial,
    "young's modulus": 100,
    "poisson's ratio": 0.25,
    "disp_bc": lambda x: np.isclose(x[0], 0) & (np.greater(x[1], 3.5) | np.less(x[1], -3.5)),
    "traction_bcs": [[(1.0, 0), in_locator]],
    "body_force": (0, 0),
    "quadrature_degree": 2,
    "petsc_options": {
        "ksp_type": "preonly",
        "pc_type": "lu",
        "pc_factor_mat_solver_type": "mumps",
    },
}

opt = {  # Topology optimization parameters
    "max_iter": 500,
    "opt_tol": 1e-5,
    "vol_frac": 0.25,
    "solid_zone": lambda x: ((np.less(x[0], 0.5) | np.greater(x[0], 9.5))
                             & np.less(x[1], 1) & np.greater(x[1], -1)),
    "void_zone": lambda x: (np.less((x[0]-2.5)**2+(x[1]-3)**2, 0.5**2)
                            | np.less((x[0]-2.5)**2+(x[1]+3)**2, 0.5**2)),
    "penalty": 3.0,
    "epsilon": 1e-6,
    "filter_radius": 0.5,
    "beta_interval": 50,
    "beta_max": 128,
    "use_oc": False,
    "move": 0.05,
    "opt_compliance": False,
    "in_spring": [in_locator, "x", 0.2],
    "out_spring": [out_locator, "x", 0.2],
    "compliance_bound": 0.5,
}

if __name__ == "__main__":
    topopt(fem, opt)

# Execute the code in parallel:
# mpirun -n 8 python3 scripts/mechanism_2d.py
