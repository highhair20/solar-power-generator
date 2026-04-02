"""
Free-Piston Stirling Engine — Multi-Objective Optimizer

Uses pymoo NSGA-II to search the design space for parameter combinations
that maximize electrical power while satisfying all engineering constraints.

This is the Leap71-style "computational engineering" loop:
  Parameters → Physics (analysis.py) → Score → Optimize → Better parameters

Design variables (what the optimizer can change):
  - Vessel bore (vessel_id), vessel wall thickness
  - Piston stroke, displacer stroke, lengths, wall, clearances
  - Operating frequency, charge pressure, phase angle
  - Cooler tube count, tube diameter, cooler length
  - Regenerator length, porosity, wire diameter
  - Hot space gap, bounce space length
  - Heater internal fins (count, height, length)
  - Displacer thermal conductivity, wall, length
  - Vessel thermal conductivity, liner conductivity, liner fraction
  - Heater head wall thickness
  - Displacer spring stiffness
  - Magnetic spring pairs, thickness, gap
  - Alternator magnet ring length
  - Coil turns, wire diameter, layers, axial length

Objectives (minimize):
  1. -P_electrical  (maximize power)
  2. dead_volume_ratio  (minimize dead volume)

Constraints (must satisfy):
  - Regenerator effectiveness > 90%
  - Total HX pressure drop < 5% of P_mean
  - Heater gas temperature drop < 80°C
  - Piston seal leakage < 5%
  - Displacer seal leakage < 5%
  - Natural frequency within 20% of operating frequency
  - Electrical output >= 60 W
  - Achievable phase angle within 15° of target
  - Magnetic spring ratio (stroke/2 / gap) < 0.33 (linear regime)

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
from analysis import evaluate, DEFAULTS, MATERIALS


# ── Material index tables ─────────────────────────────────────────
# Integer indices map to MATERIALS keys. Per-component subsets enforce
# physical constraints (e.g. no ceramic in the pressure vessel).

# Displacer: any material — ceramic is excellent for thermal isolation
DISPLACER_MATERIALS = ["ss316", "ss304", "ti64", "inconel", "ceramic"]

# Vessel: must contain ~11 bar; ceramic cannot. Ti64 is borderline at 600°C
# but the vessel runs at ambient cold-end temperature so it is acceptable.
VESSEL_MATERIALS    = ["ss316", "ss304", "ti64", "inconel"]


def _material_from_idx(keys, idx):
    """Snap a continuous optimizer index to a material key string."""
    return keys[max(0, min(int(round(idx)), len(keys) - 1))]


# ── Design variable definitions ───────────────────────────────────
# Each entry: (param_key, lower_bound, upper_bound, description)

DESIGN_VARS = [
    # ── Engine bore ────────────────────────────────────────────────────────
    # vessel_id sets the fundamental bore; all piston/displacer diameters
    # scale from it in analysis.py (piston_dia = vessel_id - 2*piston_wall - piston_cooler_gap).
    ("vessel_id",            60.0,  130.0,  "Vessel inner diameter / engine bore (mm)"),
    ("vessel_wall",           3.0,   10.0,  "Vessel wall thickness (mm)"),

    # ── Kinematics ─────────────────────────────────────────────────────────
    ("piston_stroke",         5.0,   20.0,  "Piston stroke (mm)"),
    ("displacer_stroke",      5.0,   20.0,  "Displacer stroke (mm)"),
    ("freq",                 10.0,  100.0,  "Operating frequency (Hz)"),
    ("P_mean",               10e5,   40e5,  "Charge pressure (Pa)"),
    ("phase_angle",          50.0,   90.0,  "Phase angle (deg)"),

    # ── Cold heat exchanger (cooler) ────────────────────────────────────────
    ("cooler_tube_count",    20.0,  100.0,  "Cooler tube count"),
    ("cooler_tube_dia",       1.5,    5.0,  "Cooler tube diameter (mm)"),
    ("cooler_length",        20.0,   60.0,  "Cooler length (mm)"),

    # ── Regenerator ────────────────────────────────────────────────────────
    ("regen_length",         15.0,   80.0,  "Regenerator length (mm)"),
    ("regen_porosity",        0.60,   0.85, "Regenerator porosity"),
    # Wire diameter sets mesh fineness: 0.06 mm ≈ 200-mesh, 0.25 mm ≈ 40-mesh.
    # Finer wire → better NTU but higher pressure drop.
    ("regen_wire_dia",        0.06,   0.25, "Regenerator wire diameter (mm)"),

    # ── Working spaces ──────────────────────────────────────────────────────
    ("hot_space_gap",         5.0,   25.0,  "Hot space gap (mm)"),
    ("bounce_length",        20.0,   80.0,  "Bounce space length (mm)"),

    # ── Piston geometry ─────────────────────────────────────────────────────
    ("piston_length",        15.0,   40.0,  "Piston length (mm)"),
    ("piston_wall",           4.0,   12.0,  "Piston wall thickness (mm)"),
    ("piston_clearance",      0.010,  0.075, "Piston clearance (mm radial)"),

    # ── Displacer geometry ──────────────────────────────────────────────────
    ("displacer_clearance",   0.015,  0.100, "Displacer clearance (mm radial)"),
    ("displacer_wall",        0.5,    3.0,  "Displacer wall thickness (mm)"),
    ("displacer_length",     25.0,   80.0,  "Displacer length (mm)"),

    # ── Heater head ─────────────────────────────────────────────────────────
    ("heater_int_fin_count",  8.0,   24.0,  "Heater internal fin count"),
    ("heater_int_fin_height", 10.0,  30.0,  "Heater fin height (mm)"),
    ("heater_int_fin_length", 15.0,  38.0,  "Heater fin length (mm)"),
    # Wall thickness sets conduction resistance between sand bed and gas.
    ("heater_head_wall",      2.0,    8.0,  "Heater head wall thickness (mm)"),

    # ── Thermal conductivity / insulation ───────────────────────────────────
    # ── Material selection ──────────────────────────────────────────────────
    # Integer index → material key (snapped in _evaluate).
    # Using indices instead of continuous k values ensures k AND ρ are
    # physically consistent — density drives displacer mass and resonance.
    #
    # Displacer (0-4): SS316 | SS304 | Ti-6Al-4V | Inconel 718 | Alumina ceramic
    #   Ceramic (k=2, ρ=3950) is excellent for thermal isolation; SS316 (k=16, ρ=8000)
    #   maximises conductance. Ti64 (k=7, ρ=4430) is lightest metal option.
    ("displacer_material_idx", 0.0,   4.0,  "Displacer material index (0=SS316,1=SS304,2=Ti64,3=Inconel,4=Ceramic)"),
    # Vessel outer shell (0-3): SS316 | SS304 | Ti-6Al-4V | Inconel 718
    #   No ceramic — must contain 11 bar hoop stress. Ti64 is acceptable at
    #   cold-end temperatures (vessel runs near T_cold, not T_hot).
    ("vessel_material_idx",    0.0,   3.0,  "Vessel material index (0=SS316,1=SS304,2=Ti64,3=Inconel)"),
    # Vessel inner liner: continuous k (W/mK) — separate insulation layer,
    # not load-bearing, so ceramic/alumina (k≈2) is valid here.
    ("vessel_liner_k",        2.0,    7.0,  "Vessel inner liner thermal cond (W/mK)"),
    ("vessel_liner_frac",     0.0,    0.5,  "Vessel liner fraction of wall thickness"),

    # ── Displacer spring (Fix 3) ────────────────────────────────────────────
    # Phase angle EMERGES from dynamics; k_d is the real design handle.
    # At k_d = m_d × ω², phase → 90° (optimal).
    ("displacer_spring_k",   500.0, 50000.0, "Displacer spring stiffness (N/m)"),

    # ── Magnetic spring ─────────────────────────────────────────────────────
    # More pairs → stronger spring force but higher mass penalty.
    ("mag_spring_pairs",      1.0,    4.0,  "Magnetic spring repulsive pairs"),
    # Thicker magnets → more flux but more mass and shorter stroke.
    ("mag_spring_thickness",  3.0,   10.0,  "Magnetic spring axial thickness per magnet (mm)"),
    # Equilibrium gap sets spring stiffness: smaller gap → stiffer, higher force.
    # Must exceed displacer_stroke to avoid contact.
    ("mag_spring_gap",       12.0,   60.0,  "Magnetic spring equilibrium gap (mm)"),

    # ── Linear alternator ───────────────────────────────────────────────────
    # Longer magnet ring → more flux linkage, higher EMF per turn.
    ("magnet_ring_length",   15.0,   50.0,  "Alternator magnet ring axial length (mm)"),
    ("coil_turns",          100.0,  400.0,  "Coil turns (total)"),
    ("coil_wire_dia",         0.8,    2.5,  "Coil wire diameter (mm)"),
    ("coil_layers",           2.0,    8.0,  "Coil radial layers"),
    # Longer coil → more turns in flux linkage zone; must fit within magnet stroke.
    ("coil_length",          15.0,   50.0,  "Coil axial length (mm)"),
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
        g2: dT_heater - 80               (must be < 80°C)
        g3: leak_piston_pct - 5           (must be < 5%)
        g4: leak_displacer_pct - 5        (must be < 5%)
        g5: f_resonance_error - 0.20      (f_natural within 20% of f_op;
                                           free-piston engines run at resonance —
                                           inverter decouples grid freq, not engine freq)
        g6: 60 - P_electrical             (must be >= 60 W)
        g7: phase_error_deg - 15          (achievable phase within 15° of target;
                                           ensures displacer spring k_d is physically
                                           consistent with the desired phase angle)
        g8: mag_spring_ratio - 0.33       (stroke/2 / gap must be < 0.33 to keep
                                           the magnetic spring in its linear regime;
                                           above 0.33 stiffness varies significantly
                                           across the stroke causing harmonic distortion
                                           and resonance instability)
    """

    def __init__(self):
        super().__init__(
            n_var=N_VAR,
            n_obj=2,
            n_ieq_constr=9,
            xl=LOWER,
            xu=UPPER,
        )

    def _evaluate(self, X, out, *args, **kwargs):
        n = X.shape[0]
        F = np.zeros((n, 2))
        G = np.zeros((n, 9))

        for i in range(n):
            # Build parameter dict from design vector
            params = {}
            for j, key in enumerate(PARAM_KEYS):
                val = X[i, j]
                # Integer parameters
                if key in ("cooler_tube_count", "heater_int_fin_count",
                           "coil_turns", "coil_layers", "mag_spring_pairs",
                           "displacer_material_idx", "vessel_material_idx"):
                    val = round(val)
                params[key] = val

            try:
                # Resolve material indices → string keys so analysis.py uses
                # both k AND ρ from the same material (k-only overrides removed).
                if "displacer_material_idx" in params:
                    params["displacer_material"] = _material_from_idx(
                        DISPLACER_MATERIALS, params.pop("displacer_material_idx"))
                if "vessel_material_idx" in params:
                    params["vessel_material"] = _material_from_idx(
                        VESSEL_MATERIALS, params.pop("vessel_material_idx"))
                # Ensure continuous k overrides are absent so analysis.py falls
                # back to the material lookup (which also sets correct density).
                params.pop("k_displacer", None)
                params.pop("k_vessel", None)

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
                # Resonance constraint: free-piston engines must operate AT resonance.
                # The inverter decouples output AC from the grid, but the engine mechanics
                # still require f_natural ≈ f_op for sustained self-oscillation.
                # Allow 20% tolerance to accommodate gas spring nonlinearity at amplitude.
                G[i, 5] = r.get("f_resonance_error", 0.0) - 0.20
                G[i, 6] = 60 - r["P_electrical"]
                # Phase error constraint: the spring stiffness k_d must produce a
                # phase angle within 15° of the requested phase_angle.  This enforces
                # consistency between the dynamics model and the intended design.
                G[i, 7] = r.get("phase_error_deg", 0.0) - 15.0
                # Magnetic spring linearity constraint: keep stroke/2 / gap < 0.33
                # so the spring operates in its near-linear regime. The optimizer
                # can satisfy this by increasing gap, reducing stroke, or both.
                G[i, 8] = r.get("mag_spring_ratio", 0.0) - 0.33

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
        print(f"  {N_VAR} design variables, 2 objectives, 9 constraints")
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
            if key in ("cooler_tube_count", "heater_int_fin_count",
                       "coil_turns", "coil_layers", "mag_spring_pairs",
                       "displacer_material_idx", "vessel_material_idx"):
                val = round(val)
            params[key] = val

        if "displacer_material_idx" in params:
            params["displacer_material"] = _material_from_idx(
                DISPLACER_MATERIALS, params.pop("displacer_material_idx"))
        if "vessel_material_idx" in params:
            params["vessel_material"] = _material_from_idx(
                VESSEL_MATERIALS, params.pop("vessel_material_idx"))
        params.pop("k_displacer", None)
        params.pop("k_vessel", None)

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
        # Material indices are resolved to names in extract_designs; look up
        # the resolved name from params if present, else use raw value.
        if key == "displacer_material_idx":
            resolved = best["params"].get("displacer_material", "—")
            mat = MATERIALS.get(resolved, {})
            print(f"    {'Displacer material':35s}  {resolved:>10s}  "
                  f"(k={mat.get('k','?')} W/mK, ρ={mat.get('rho','?')} kg/m³)")
            continue
        if key == "vessel_material_idx":
            resolved = best["params"].get("vessel_material", "—")
            mat = MATERIALS.get(resolved, {})
            print(f"    {'Vessel material':35s}  {resolved:>10s}  "
                  f"(k={mat.get('k','?')} W/mK, ρ={mat.get('rho','?')} kg/m³)")
            continue
        val = best["params"].get(key)
        if val is None:
            continue
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
        "VESSEL_ID": ("vessel_id", "mm — engine bore"),
        "VESSEL_WALL": ("vessel_wall", "mm"),
        "VESSEL_MATERIAL": ("vessel_material", ""),
        "DISPLACER_MATERIAL": ("displacer_material", ""),
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
        "HEATER_HEAD_WALL": ("heater_head_wall", "mm"),
        "MAG_SPRING_PAIRS": ("mag_spring_pairs", "repulsive pairs"),
        "MAG_SPRING_THICKNESS": ("mag_spring_thickness", "mm per magnet"),
        "MAG_SPRING_GAP": ("mag_spring_gap", "mm equilibrium gap"),
        "MAGNET_RING_LENGTH": ("magnet_ring_length", "mm"),
        "COIL_TURNS": ("coil_turns", "total turns"),
        "COIL_WIRE_DIA": ("coil_wire_dia", "mm"),
        "COIL_LAYERS": ("coil_layers", "radial layers"),
        "COIL_LENGTH": ("coil_length", "mm"),
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
