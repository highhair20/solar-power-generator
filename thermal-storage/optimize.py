"""
Thermal Storage (Sand Battery) — Multi-Objective Optimizer

Finds vessel geometry, sand mass, and insulation specification that
maximise stored energy capacity while minimising standby self-discharge.
Uses the shared NSGA-II infrastructure from src/utils/simulation/optimization/base.py.

Design variables:
  - Sand mass, vessel diameter, aspect ratio
  - Insulation thickness and thermal conductivity
  - Operating temperature range, rated discharge power

Objectives (minimise):
  1. -E_capacity_kWh           (maximise storage capacity)
  2.  self_discharge_pct_per_h (minimise standby losses)

Constraints:
  - U_wall < 0.10 W/m²·K
  - Discharge duration > 4 h at rated power
  - Vessel fill fraction < 0.85 (structural headroom)
  - SOC after 12 h standby > 0.95  (< 5% self-discharge per 12 h)
  - T_hot < 1273 K (sand thermal limit)
  - T_cold < T_hot - 50 K (minimum useful temperature differential)

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
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
from src.utils.simulation.optimization.base import run_nsga2, decode_design_vector


# ── Design variable definitions ──────────────────────────────────
# Each entry: (param_key, lower_bound, upper_bound, description)

DESIGN_VARS = [
    ("m_medium_kg",        200.0,  3000.0,  "Sand mass (kg)"),
    ("D_vessel_m",           0.40,    2.00,  "Vessel inner diameter (m)"),
    ("AR_vessel",            1.0,     5.0,   "Vessel aspect ratio H/D"),
    ("t_insulation_m",       0.05,    0.40,  "Insulation thickness (m)"),
    ("k_insulation_W_mK",    0.015,   0.150, "Insulation conductivity (W/m·K)"),
    ("T_hot_K",            773.0,  1073.0,   "Peak storage temperature (K)"),
    ("T_cold_K",           373.0,   573.0,   "Discharge floor temperature (K)"),
    ("q_discharge_W",      100.0,  1000.0,   "Rated discharge power (W)"),
]

INT_KEYS = set()   # no integer parameters in the storage model

N_VAR = len(DESIGN_VARS)
LOWER = np.array([v[1] for v in DESIGN_VARS])
UPPER = np.array([v[2] for v in DESIGN_VARS])


class StorageProblem(Problem):
    """pymoo Problem for multi-objective thermal storage optimisation.

    Objectives (both minimised by NSGA-II):
        f0: -E_capacity_kWh            (maximise storage capacity)
        f1:  self_discharge_pct_per_h  (minimise standby losses)

    Constraints (g ≤ 0 means satisfied):
        g0: U_wall - 0.10              U-value target (< 0.10 W/m²·K)
        g1: 4.0 - t_discharge_h        discharge duration > 4 h
        g2: fill_fraction - 0.85       vessel not overfull
        g3: 0.95 - SOC_after_12h       less than 5% loss per 12 h standby
        g4: T_hot_K - 1273             sand thermal limit
        g5: T_cold_K - (T_hot_K - 50) T_cold must be at least 50 K below T_hot
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

                F[i, 0] = -r["E_capacity_kWh"]
                F[i, 1] = r["self_discharge_pct_per_h"]

                G[i, 0] = r["U_wall_W_m2K"] - 0.10
                G[i, 1] = 4.0 - r["t_discharge_h"]
                G[i, 2] = r["fill_fraction"] - 0.85
                G[i, 3] = 0.95 - r["SOC_after_12h"]
                G[i, 4] = params["T_hot_K"] - 1273.0
                G[i, 5] = params["T_cold_K"] - (params["T_hot_K"] - 50.0)

            except (ValueError, ZeroDivisionError, OverflowError):
                F[i, 0] = 0.0
                F[i, 1] = 999.0
                G[i, :] = 100.0

        out["F"] = F
        out["G"] = G


def extract_designs(result, top_n=10):
    """Extract top designs from result, sorted by storage capacity (highest first)."""
    if result.F is None or len(result.F) == 0:
        print("No feasible solutions found. Try more generations or relaxed constraints.")
        return []

    # F[:,0] is -E_capacity_kWh → ascending sort = highest capacity first
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

    print("\n" + "=" * 100)
    print("OPTIMISED DESIGNS — Pareto Front (sorted by storage capacity)")
    print("=" * 100)
    print(f"{'#':>3}  {'E_cap':>7}  {'%/h':>6}  {'12h%':>5}  {'U_wall':>6}  "
          f"{'t_dis':>5}  {'Chks':>4}  "
          f"{'Mass':>6}  {'D':>5}  {'H/D':>4}  {'t_ins':>5}  {'T_hot':>5}  {'T_cold':>6}")
    print("-" * 100)

    for d in designs:
        p = d["params"]
        r = d["metrics"]
        print(f"{d['rank']:>3}  "
              f"{r['E_capacity_kWh']:>6.2f}kWh  "
              f"{r['self_discharge_pct_per_h']:>5.3f}%  "
              f"{r['SOC_after_12h']*100:>4.1f}%  "
              f"{r['U_wall_W_m2K']:>6.4f}  "
              f"{r['t_discharge_h']:>4.1f}h  "
              f"{r['checks_passed']}/{r['checks_total']}  "
              f"{p['m_medium_kg']:>5.0f}kg "
              f"{p['D_vessel_m']*1000:>4.0f}mm "
              f"{p['AR_vessel']:>4.1f} "
              f"{p['t_insulation_m']*1000:>4.0f}mm "
              f"{p['T_hot_K']-273.15:>4.0f}C "
              f"{p['T_cold_K']-273.15:>5.0f}C")

    best = designs[0]
    print(f"\n{'=' * 100}")
    print("BEST DESIGN (#1) — DETAILED REPORT")
    print(f"{'=' * 100}")
    print("\n  Design Variables:")
    for key, lo, hi, desc in DESIGN_VARS:
        val = best["params"][key]
        default = DEFAULTS.get(key, "—")
        if isinstance(default, (int, float)):
            change = (f"({default:>8.2f} -> {val:>8.2f})"
                      if abs(val - default) > 1e-9 else "(unchanged)")
        else:
            change = ""
        print(f"    {desc:40s}  {val:>10.3f}  {change}")

    print("\n  Performance:")
    print_report(best["params"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimise thermal storage (sand battery)")
    parser.add_argument("--gens",   type=int, default=100, help="Number of generations")
    parser.add_argument("--pop",    type=int, default=120, help="Population size")
    parser.add_argument("--seed",   type=int, default=42,  help="Random seed")
    parser.add_argument("--top",    type=int, default=10,  help="Top designs to show")
    parser.add_argument("--report", action="store_true",   help="Detailed report for best design")
    args = parser.parse_args()

    result = run_nsga2(
        StorageProblem(),
        pop_size=args.pop,
        n_gen=args.gens,
        seed=args.seed,
    )

    designs = extract_designs(result, top_n=args.top)
    print_designs(designs)
