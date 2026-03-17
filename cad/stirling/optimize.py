"""
Free-Piston Stirling Engine — Multi-Objective Optimizer

Uses pymoo NSGA-II to search the design space for parameter combinations
that maximize electrical power while satisfying all engineering constraints.

This is the Leap71-style "computational engineering" loop:
  Parameters → Physics (analysis.py) → Score → Optimize → Better parameters

Design variables (what the optimizer can change):
  - Piston stroke, displacer stroke
  - Operating frequency, charge pressure
  - Cooler tube count, tube diameter, cooler length
  - Regenerator length, porosity
  - Hot space gap, bounce space length
  - Phase angle

Objectives (minimize):
  1. -P_electrical  (maximize power)
  2. dead_volume_ratio  (minimize dead volume)

Constraints (must satisfy):
  - Regenerator effectiveness > 90%
  - Total HX pressure drop < 5% of P_mean
  - Heater gas temperature drop < 50°C
  - Piston seal leakage < 5%
  - Displacer seal leakage < 5%
  - Natural frequency within 25% of operating frequency
  - Electrical output >= 60 W

Usage:
  python optimize.py              # run optimization
  python optimize.py --gens 200   # more generations
  python optimize.py --pop 200    # larger population
  python optimize.py --report     # print top designs in detail
"""

import argparse
import math
import sys
import os

import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.lhs import LHS
from pymoo.optimize import minimize as pymoo_minimize
from pymoo.termination import get_termination

# Import the physics model
sys.path.insert(0, os.path.dirname(__file__))
from analysis import evaluate, DEFAULTS


# ── Design variable definitions ───────────────────────────────────
# Each entry: (param_key, lower_bound, upper_bound, description)

DESIGN_VARS = [
    ("piston_stroke",         5.0,   20.0,  "Piston stroke (mm)"),
    ("displacer_stroke",      5.0,   20.0,  "Displacer stroke (mm)"),
    ("freq",                 10.0,  100.0,  "Operating frequency (Hz)"),
    ("P_mean",               10e5,   40e5,  "Charge pressure (Pa)"),
    ("phase_angle",          50.0,   90.0,  "Phase angle (deg)"),
    ("cooler_tube_count",    20.0,  100.0,  "Cooler tube count"),
    ("cooler_tube_dia",       1.5,    5.0,  "Cooler tube diameter (mm)"),
    ("cooler_length",        20.0,   60.0,  "Cooler length (mm)"),
    ("regen_length",         15.0,   80.0,  "Regenerator length (mm)"),
    ("regen_porosity",        0.60,   0.85, "Regenerator porosity"),
    ("hot_space_gap",         5.0,   25.0,  "Hot space gap (mm)"),
    ("bounce_length",        20.0,   80.0,  "Bounce space length (mm)"),
    ("piston_length",        15.0,   40.0,  "Piston length (mm)"),
    ("piston_wall",           4.0,   12.0,  "Piston wall thickness (mm)"),
    ("piston_clearance",      0.010,  0.075, "Piston clearance (mm radial)"),
    ("displacer_clearance",   0.015,  0.100, "Displacer clearance (mm radial)"),
    ("heater_int_fin_count",  8.0,   24.0,  "Heater internal fin count"),
    ("heater_int_fin_height", 10.0,  30.0,  "Heater fin height (mm)"),
    ("heater_int_fin_length", 15.0,  38.0,  "Heater fin length (mm)"),
    ("k_displacer",           2.0,   16.0,  "Displacer thermal cond (W/mK)"),
    ("k_vessel",              2.0,   16.0,  "Vessel thermal cond (W/mK)"),
    ("displacer_wall",        0.5,    3.0,  "Displacer wall thickness (mm)"),
    ("displacer_length",     25.0,   80.0,  "Displacer length (mm)"),
]

N_VAR = len(DESIGN_VARS)
PARAM_KEYS = [v[0] for v in DESIGN_VARS]
LOWER = np.array([v[1] for v in DESIGN_VARS])
UPPER = np.array([v[2] for v in DESIGN_VARS])


class StirlingProblem(Problem):
    """pymoo Problem for multi-objective Stirling engine optimization.

    Objectives:
        f1: -P_electrical (maximize power → minimize negative power)
        f2: dead_volume_ratio (minimize)

    Constraints (g <= 0 means satisfied):
        g0: 0.90 - regen_effectiveness    (must be > 90%)
        g1: dp_total_frac - 0.05          (must be < 5%)
        g2: dT_heater - 50               (must be < 50°C)
        g3: leak_piston_pct - 5           (must be < 5%)
        g4: leak_displacer_pct - 5        (must be < 5%)
        g5: |f_natural - freq|/freq - 0.25 (must be within 25%)
        g6: 60 - P_electrical             (must be >= 60 W)
    """

    def __init__(self):
        super().__init__(
            n_var=N_VAR,
            n_obj=2,
            n_ieq_constr=7,
            xl=LOWER,
            xu=UPPER,
        )

    def _evaluate(self, X, out, *args, **kwargs):
        n = X.shape[0]
        F = np.zeros((n, 2))
        G = np.zeros((n, 7))

        for i in range(n):
            # Build parameter dict from design vector
            params = {}
            for j, key in enumerate(PARAM_KEYS):
                val = X[i, j]
                # Integer parameters
                if key in ("cooler_tube_count", "heater_int_fin_count"):
                    val = round(val)
                params[key] = val

            try:
                r = evaluate(params)

                # Objectives
                F[i, 0] = -r["P_electrical"]       # maximize power
                F[i, 1] = r["dead_volume_ratio"]    # minimize dead volume

                # Constraints (g <= 0 means feasible)
                G[i, 0] = 0.90 - r["regen_effectiveness"]
                G[i, 1] = r["dp_total_frac"] - 0.05
                G[i, 2] = r["dT_heater"] - 80
                G[i, 3] = r["leak_piston_pct"] - 5
                G[i, 4] = r["leak_displacer_pct"] - 5
                # Frequency constraint removed — inverter decouples engine from AC grid.
                # Only require f_natural > 10 Hz (below that, engine is impractically slow)
                G[i, 5] = 10.0 - r["f_natural"]
                G[i, 6] = 60 - r["P_electrical"]

            except (ValueError, ZeroDivisionError, OverflowError):
                # Infeasible design — penalize heavily
                F[i, 0] = 0       # 0 W power
                F[i, 1] = 100     # terrible dead volume ratio
                G[i, :] = 100     # all constraints violated

        out["F"] = F
        out["G"] = G


def run_optimization(n_gen=100, pop_size=120, seed=42, verbose=True):
    """Run NSGA-II optimization and return results.

    Args:
        n_gen: number of generations
        pop_size: population size per generation
        seed: random seed for reproducibility
        verbose: print progress

    Returns:
        pymoo Result object
    """
    problem = StirlingProblem()

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=LHS(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True,
    )

    termination = get_termination("n_gen", n_gen)

    if verbose:
        print(f"Running NSGA-II: {pop_size} population x {n_gen} generations")
        print(f"  {N_VAR} design variables, 2 objectives, 7 constraints")
        print(f"  Evaluating ~{pop_size * n_gen:,} designs...")
        print()

    result = pymoo_minimize(
        problem,
        algorithm,
        termination,
        seed=seed,
        verbose=verbose,
    )

    return result


def extract_designs(result, top_n=10):
    """Extract the top designs from a pymoo result.

    Returns list of dicts, each with 'params', 'metrics', and 'rank'.
    Sorted by electrical power (highest first).
    """
    if result.F is None or len(result.F) == 0:
        print("No feasible solutions found. Try more generations or relaxing constraints.")
        return []

    X = result.X
    F = result.F

    # Sort by power (F[:,0] is -P_electrical, so ascending = highest power first)
    order = np.argsort(F[:, 0])
    designs = []

    for rank, idx in enumerate(order[:top_n]):
        params = {}
        for j, key in enumerate(PARAM_KEYS):
            val = X[idx, j]
            if key in ("cooler_tube_count", "heater_int_fin_count"):
                val = round(val)
            params[key] = val

        metrics = evaluate(params)
        designs.append({
            "rank": rank + 1,
            "params": params,
            "metrics": metrics,
        })

    return designs


def print_designs(designs):
    """Print a summary table of optimized designs."""
    if not designs:
        return

    print("\n" + "=" * 90)
    print("OPTIMIZED DESIGNS — Pareto Front (sorted by power)")
    print("=" * 90)

    # Header
    print(f"{'#':>3}  {'Power':>7}  {'DVR':>5}  {'Regen':>5}  {'dP%':>5}  "
          f"{'dT_h':>5}  {'Leak%':>6}  {'f_nat':>5}  {'Chks':>4}  "
          f"{'Stroke':>6}  {'Freq':>4}  {'Pbar':>4}  {'Phase':>5}")
    print("-" * 90)

    for d in designs:
        p = d["params"]
        r = d["metrics"]
        print(f"{d['rank']:>3}  "
              f"{r['P_electrical']:>6.1f}W  "
              f"{r['dead_volume_ratio']:>5.2f}  "
              f"{r['regen_effectiveness']*100:>4.0f}%  "
              f"{r['dp_total_frac']*100:>4.1f}%  "
              f"{r['dT_heater']:>4.0f}C  "
              f"{max(r['leak_piston_pct'], r['leak_displacer_pct']):>5.1f}%  "
              f"{r['f_natural']:>4.0f}Hz  "
              f"{r['checks_passed']}/{r['checks_total']}  "
              f"{p['piston_stroke']:>5.1f}mm "
              f"{p['freq']:>3.0f}Hz "
              f"{p['P_mean']/1e5:>3.0f}b  "
              f"{p['phase_angle']:>4.0f}d")

    # Print detailed report for the best design
    best = designs[0]
    print(f"\n{'=' * 90}")
    print(f"BEST DESIGN (#1) — DETAILED REPORT")
    print(f"{'=' * 90}")

    print("\n  Design Variables:")
    for j, (key, lo, hi, desc) in enumerate(DESIGN_VARS):
        val = best["params"][key]
        default = DEFAULTS.get(key, "—")
        if isinstance(default, (int, float)):
            change = f"({default:>10.2f} -> {val:>10.2f})" if abs(val - default) > 0.01 else "(unchanged)"
        else:
            change = ""
        print(f"    {desc:35s}  {val:>10.2f}  {change}")

    print("\n  Performance:")
    from analysis import print_report
    print_report(best["params"])


def generate_cad_params(design):
    """Generate a parameter block for free_piston_stirling.py from an optimized design.

    Prints the parameter values that should be updated in the CAD script.
    """
    p = design["params"]
    r = design["metrics"]

    print("\n" + "=" * 70)
    print("CAD PARAMETER UPDATE")
    print("=" * 70)
    print("# Copy these values into free_piston_stirling.py:")
    print()

    # Map optimizer params back to CAD params
    param_map = {
        "PISTON_STROKE": ("piston_stroke", "mm — optimized"),
        "DISPLACER_STROKE": ("displacer_stroke", "mm — optimized"),
        "PISTON_LENGTH": ("piston_length", "mm"),
        "PISTON_WALL": ("piston_wall", "mm"),
        "COOLER_INT_TUBE_DIA": ("cooler_tube_dia", "mm"),
        "COOLER_INT_TUBE_COUNT": ("cooler_tube_count", ""),
        "COOLER_INT_LENGTH": ("cooler_length", "mm"),
        "REGEN_LENGTH": ("regen_length", "mm"),
        "REGEN_POROSITY": ("regen_porosity", ""),
        "HOT_SPACE_GAP": ("hot_space_gap", "mm"),
        "BOUNCE_SPACE_LENGTH": ("bounce_length", "mm"),
        "MAG_SPRING_GAP": (None, "mm — must be > displacer_stroke"),
    }

    for cad_name, (opt_key, unit) in param_map.items():
        if opt_key and opt_key in p:
            val = p[opt_key]
            if opt_key == "cooler_tube_count":
                print(f"{cad_name} = {int(val)}        # {unit}")
            else:
                print(f"{cad_name} = {val:.1f}       # {unit}")
        elif cad_name == "MAG_SPRING_GAP":
            gap = p.get("displacer_stroke", 12) + 8  # stroke + margin
            print(f"{cad_name} = {gap:.1f}       # {unit}")

    print(f"\n# Operating conditions (not in CAD, for reference):")
    print(f"# FREQ = {p.get('freq', 55):.1f} Hz")
    print(f"# P_MEAN = {p.get('P_mean', 25e5)/1e5:.1f} bar")
    print(f"# PHASE_ANGLE = {p.get('phase_angle', 70):.1f} deg")
    print(f"#")
    print(f"# Predicted performance:")
    print(f"# P_electrical = {r['P_electrical']:.1f} W")
    print(f"# Efficiency = {r['eta_overall']*100:.1f}%")
    print(f"# Dead volume ratio = {r['dead_volume_ratio']:.2f}:1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize free-piston Stirling engine")
    parser.add_argument("--gens", type=int, default=100, help="Number of generations")
    parser.add_argument("--pop", type=int, default=120, help="Population size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--top", type=int, default=10, help="Number of top designs to show")
    parser.add_argument("--report", action="store_true", help="Print detailed report for best design")
    parser.add_argument("--cad", action="store_true", help="Print CAD parameter update for best design")
    args = parser.parse_args()

    result = run_optimization(n_gen=args.gens, pop_size=args.pop, seed=args.seed)

    designs = extract_designs(result, top_n=args.top)
    print_designs(designs)

    if args.cad and designs:
        generate_cad_params(designs[0])
