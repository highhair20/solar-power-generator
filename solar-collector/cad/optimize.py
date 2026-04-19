"""
Parabolic Dish Collector — Multi-Objective Optimizer

Finds dish and receiver geometries that maximise net thermal output
(q_collector_W) while minimising heat-loss fraction. Uses the shared
NSGA-II infrastructure from src/utils/simulation/optimization/base.py.

Design variables:
  - Dish aperture diameter, focal ratio
  - Receiver aperture, cavity diameter and depth
  - Cavity wall emissivity, tracking error, mirror reflectivity

Objectives (minimise):
  1. -q_collector_W    (maximise net thermal output)
  2.  Q_loss_frac      (minimise heat loss as fraction of Q_solar)

Constraints:
  - Concentration ratio C > 500
  - Intercept factor γ > 0.90
  - Receiver aperture fits inside cavity  (D_ap < 0.80 × D_cav)
  - Cavity aspect ratio D_cav / L_cav in [0.5, 2.0]
  - Net output q_collector_W > 200 W

Usage:
  python optimize.py              # run with defaults (100 gen, pop 120)
  python optimize.py --gens 150   # more generations
  python optimize.py --pop 150    # larger population
  python optimize.py --report     # detailed report for best design
"""

import argparse
import sys
import os
from pathlib import Path

import numpy as np
from pymoo.core.problem import Problem

# Local physics model (same directory)
sys.path.insert(0, os.path.dirname(__file__))
from analysis import evaluate, DEFAULTS, print_report

# Shared optimizer infrastructure (project root → src package)
_project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_project_root))
from src.utils.simulation.optimization.base import run_nsga2, decode_design_vector


# ── Design variable definitions ──────────────────────────────────
# Each entry: (param_key, lower_bound, upper_bound, description)

DESIGN_VARS = [
    ("D_aperture_m",           0.50,  2.00,  "Dish aperture diameter (m)"),
    ("focal_ratio",            0.30,  0.80,  "Focal ratio f/D"),
    ("D_aperture_receiver_m",  0.020, 0.120, "Receiver aperture diameter (m)"),
    ("D_cavity_m",             0.050, 0.200, "Cavity inner diameter (m)"),
    ("L_cavity_m",             0.030, 0.150, "Cavity depth (m)"),
    ("epsilon_receiver",       0.05,  0.35,  "Cavity wall emissivity"),
    ("sigma_tracking_mrad",    1.0,   10.0,  "Tracking error 1σ (mrad)"),
    ("rho_mirror",             0.85,  0.95,  "Mirror reflectivity"),
]

INT_KEYS = set()   # no integer parameters in the collector model

N_VAR = len(DESIGN_VARS)
LOWER = np.array([v[1] for v in DESIGN_VARS])
UPPER = np.array([v[2] for v in DESIGN_VARS])


class CollectorProblem(Problem):
    """pymoo Problem for multi-objective collector optimisation.

    Objectives (both minimised by NSGA-II):
        f0: -q_collector_W    (maximise net thermal output)
        f1:  Q_loss_frac      (minimise heat loss fraction)

    Constraints (g ≤ 0 means satisfied):
        g0: 500 - C                         concentration ratio > 500
        g1: 0.90 - gamma                    intercept factor > 90%
        g2: D_ap/D_cav - 0.80              aperture fits inside cavity
        g3: 0.5 - D_cav/L_cav             cavity not too deep (D/L > 0.5)
        g4: D_cav/L_cav - 2.0             cavity not too shallow (D/L < 2.0)
        g5: 200 - q_collector_W            minimum useful output 200 W
    """

    def __init__(self):
        super().__init__(
            n_var=N_VAR,
            n_obj=2,
            n_ieq_constr=6,
            xl=LOWER,
            xu=UPPER,
        )

    def _evaluate(self, X, out, *args, **kwargs):
        n = X.shape[0]
        F = np.zeros((n, 2))
        G = np.zeros((n, 6))

        for i in range(n):
            params = decode_design_vector(X[i], DESIGN_VARS, INT_KEYS)
            try:
                r = evaluate(params)

                F[i, 0] = -r["q_collector_W"]
                F[i, 1] = r["Q_loss_frac"]

                D_L = params["D_cavity_m"] / params["L_cavity_m"]
                G[i, 0] = 500.0 - r["C"]
                G[i, 1] = 0.90 - r["gamma"]
                G[i, 2] = (params["D_aperture_receiver_m"] /
                            params["D_cavity_m"]) - 0.80
                G[i, 3] = 0.5 - D_L
                G[i, 4] = D_L - 2.0
                G[i, 5] = 200.0 - r["q_collector_W"]

            except (ValueError, ZeroDivisionError, OverflowError):
                F[i, 0] = 0.0
                F[i, 1] = 1.0
                G[i, :] = 100.0

        out["F"] = F
        out["G"] = G


def extract_designs(result, top_n=10):
    """Extract top designs from result, sorted by net thermal output (highest first)."""
    if result.F is None or len(result.F) == 0:
        print("No feasible solutions found. Try more generations or relaxed constraints.")
        return []

    # F[:,0] is -q_collector_W → ascending sort = highest power first
    order = np.argsort(result.F[:, 0])
    designs = []
    for rank, idx in enumerate(order[:top_n]):
        params = decode_design_vector(result.X[idx], DESIGN_VARS, INT_KEYS)
        metrics = evaluate(params)
        designs.append({"rank": rank + 1, "params": params, "metrics": metrics})
    return designs


def print_designs(designs):
    """Print summary table then detailed report for the best design."""
    if not designs:
        return

    print("\n" + "=" * 90)
    print("OPTIMISED DESIGNS — Pareto Front (sorted by net thermal output)")
    print("=" * 90)
    print(f"{'#':>3}  {'q_coll':>7}  {'η_coll':>6}  {'η_opt':>5}  {'C':>5}  "
          f"{'γ':>5}  {'Loss%':>5}  {'Chks':>4}  "
          f"{'D_dish':>6}  {'f/D':>4}  {'D_ap':>5}  {'ε_cav':>5}")
    print("-" * 90)

    for d in designs:
        p = d["params"]
        r = d["metrics"]
        print(f"{d['rank']:>3}  "
              f"{r['q_collector_W']:>6.1f}W  "
              f"{r['eta_collector']*100:>5.1f}%  "
              f"{r['eta_optical']*100:>4.0f}%  "
              f"{r['C']:>5.0f}  "
              f"{r['gamma']*100:>4.0f}%  "
              f"{r['Q_loss_frac']*100:>4.1f}%  "
              f"{r['checks_passed']}/{r['checks_total']}  "
              f"{p['D_aperture_m']*1000:>5.0f}mm "
              f"{p['focal_ratio']:>4.2f} "
              f"{p['D_aperture_receiver_m']*1000:>4.0f}mm "
              f"{p['epsilon_receiver']:>5.3f}")

    best = designs[0]
    print(f"\n{'=' * 90}")
    print("BEST DESIGN (#1) — DETAILED REPORT")
    print(f"{'=' * 90}")
    print("\n  Design Variables:")
    for key, lo, hi, desc in DESIGN_VARS:
        val = best["params"][key]
        default = DEFAULTS.get(key, "—")
        if isinstance(default, (int, float)):
            change = (f"({default:>8.3f} -> {val:>8.3f})"
                      if abs(val - default) > 1e-9 else "(unchanged)")
        else:
            change = ""
        print(f"    {desc:40s}  {val:>10.4f}  {change}")

    print("\n  Performance:")
    print_report(best["params"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimise parabolic dish collector")
    parser.add_argument("--gens",   type=int, default=100, help="Number of generations")
    parser.add_argument("--pop",    type=int, default=120, help="Population size")
    parser.add_argument("--seed",   type=int, default=42,  help="Random seed")
    parser.add_argument("--top",    type=int, default=10,  help="Top designs to show")
    parser.add_argument("--report", action="store_true",   help="Detailed report for best design")
    args = parser.parse_args()

    result = run_nsga2(
        CollectorProblem(),
        pop_size=args.pop,
        n_gen=args.gens,
        seed=args.seed,
    )

    designs = extract_designs(result, top_n=args.top)
    print_designs(designs)
