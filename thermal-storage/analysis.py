"""
Thermal Storage (Sand Battery) — Thermodynamic Model

Computes storage capacity, standby losses, and discharge duration from
vessel geometry and insulation specification.

Physics modeled:
1. Temperature-dependent specific heat of silica sand (polynomial fit to NIST data)
2. Stored energy: m × c̄_p × (T_hot - T_cold), where c̄_p is mass-averaged
3. Insulation thermal resistance: cylindrical wall (log-mean) + flat end caps
4. Standby self-discharge: Q_loss / E_stored at full charge
5. Discharge duration at rated power

Interface outputs (project CLAUDE.md):
  T_storage_hot_K    Hot-side temperature available to the engine [K]
  T_storage_cold_K   Cold-side return temperature [K]
  q_discharge_W      Thermal power discharged to engine (design input) [W]
  E_stored_kWh       Current stored energy (at full charge) [kWh]
  SOC                State of charge after 12 h standby (0=empty, 1=full) [–]

References:
- Waples & Waples, "A Review of Specific Heats of Rocks, Minerals, and
  Subsurface Fluids", Natural Resources Research 13 (2004)
- Hasnain, "Review on sustainable thermal energy storage technologies",
  Energy Conversion and Management 39 (1998)
- Incropera & DeWitt, "Fundamentals of Heat and Mass Transfer" (7th ed.),
  ch. 3 (cylindrical and composite walls)
"""

import math

# ── Material: silica sand ─────────────────────────────────────────

RHO_BULK_KG_M3 = 1550.0   # bulk density of dry silica sand [kg/m³]


def cp_sand_J_kgK(T_K):
    """Temperature-dependent specific heat of silica sand [J/kg·K].

    Piecewise linear fit to quartz/silica data 300–1100 K:
      300–800 K: c_p = 730 + 0.39 × (T - 300)   (rises with temperature)
      800–1100 K: c_p ≈ 925 + 0.05 × (T - 800)  (flattens near α-β quartz
                                                    transition at ~846°C)

    Ref: Waples & Waples (2004); NIST WebBook for quartz SiO₂.
    """
    if T_K <= 300:
        return 730.0
    elif T_K <= 800:
        return 730.0 + 0.39 * (T_K - 300.0)
    else:
        return 925.0 + 0.05 * (T_K - 800.0)


def mean_cp_sand_J_kgK(T_cold_K, T_hot_K, n_steps=50):
    """Mass-averaged specific heat of sand between T_cold and T_hot [J/kg·K].

    Integrates cp(T) over the temperature range using n_steps trapezoid steps.
    """
    if T_hot_K <= T_cold_K:
        return cp_sand_J_kgK((T_hot_K + T_cold_K) / 2.0)
    T_vals = [T_cold_K + (T_hot_K - T_cold_K) * i / n_steps
              for i in range(n_steps + 1)]
    return sum(cp_sand_J_kgK(T) for T in T_vals) / (n_steps + 1)


# ── Default design parameters ──────────────────────────────────────

DEFAULTS = {
    # Vessel geometry
    "D_vessel_m":          0.80,    # vessel inner diameter [m]
    "AR_vessel":           2.0,     # height / diameter aspect ratio [–]

    # Storage medium
    "m_medium_kg":         800.0,   # sand mass [kg]
    "rho_bulk_kg_m3":      RHO_BULK_KG_M3,

    # Insulation
    "t_insulation_m":      0.15,    # insulation thickness [m]
    "k_insulation_W_mK":   0.05,    # insulation thermal conductivity [W/m·K]
    # Typical values:  mineral wool blanket: 0.040
    #                  ceramic fibre blanket: 0.060–0.120
    #                  aerogel composite:     0.015–0.020

    # Operating temperatures
    "T_hot_K":             873.15,  # peak storage temperature [K] (600°C)
    "T_cold_K":            473.15,  # discharge floor temperature [K] (200°C)
    "T_amb_K":             298.15,  # ambient temperature [K] (25°C)

    # Discharge
    "q_discharge_W":       550.0,   # rated thermal power to engine [W]
    "eta_discharge":       0.95,    # heat transfer effectiveness during discharge [–]
}


def evaluate(params=None):
    """Evaluate thermal storage performance from geometry and insulation spec.

    Args:
        params: dict of design parameters (missing keys use DEFAULTS)

    Returns:
        dict with capacity, losses, discharge duration, and validation checks
    """
    p = {**DEFAULTS, **(params or {})}

    D = p["D_vessel_m"]
    H = D * p["AR_vessel"]           # vessel inner height [m]
    r_i = D / 2.0                    # inner radius [m]
    t_ins = p["t_insulation_m"]
    k_ins = p["k_insulation_W_mK"]
    r_o = r_i + t_ins                # outer radius (insulation outer surface) [m]

    # ── Vessel geometry ────────────────────────────────────────────
    V_vessel_m3 = math.pi / 4.0 * D**2 * H              # inner volume [m³]
    A_outer_cyl_m2 = 2.0 * math.pi * r_o * H            # cylindrical outer area [m²]
    A_outer_cap_m2 = math.pi * r_o**2                    # one end cap outer area [m²]
    A_outer_total_m2 = A_outer_cyl_m2 + 2.0 * A_outer_cap_m2

    # ── Energy capacity ────────────────────────────────────────────
    cp_avg = mean_cp_sand_J_kgK(p["T_cold_K"], p["T_hot_K"])
    E_capacity_J = p["m_medium_kg"] * cp_avg * (p["T_hot_K"] - p["T_cold_K"])
    E_capacity_kWh = E_capacity_J / 3_600_000.0

    # ── Insulation thermal conductance (UA) ────────────────────────
    # Cylindrical wall: UA_cyl = 2π k L / ln(r_o / r_i)   [W/K]
    # End caps (×2):    UA_cap = k × A_inner_cap / t_ins   [W/K] per cap
    A_inner_cap_m2 = math.pi * r_i**2

    if r_o > r_i * 1.001:
        UA_cyl = 2.0 * math.pi * k_ins * H / math.log(r_o / r_i)
    else:
        # Thin-wall limit (avoids log(1) = 0)
        UA_cyl = k_ins * 2.0 * math.pi * r_i * H / t_ins

    UA_caps = 2.0 * k_ins * A_inner_cap_m2 / t_ins

    UA_total = UA_cyl + UA_caps      # total thermal conductance [W/K]
    U_wall_W_m2K = UA_total / A_outer_total_m2   # referred to outer surface [W/m²·K]

    # ── Standby heat loss ──────────────────────────────────────────
    Q_loss_standby_W = UA_total * (p["T_hot_K"] - p["T_amb_K"])

    self_discharge_pct_per_h = (
        Q_loss_standby_W * 3600.0 / E_capacity_J * 100.0
        if E_capacity_J > 0 else 999.0
    )

    # State of charge after 12 hours of standby at full charge, no input
    energy_lost_12h_J = Q_loss_standby_W * 12.0 * 3600.0
    SOC_after_12h = max(0.0, 1.0 - energy_lost_12h_J / E_capacity_J) if E_capacity_J > 0 else 0.0

    # ── Discharge performance ──────────────────────────────────────
    E_usable_J = E_capacity_J * p["eta_discharge"]
    t_discharge_h = (E_usable_J / (p["q_discharge_W"] * 3600.0)
                     if p["q_discharge_W"] > 0 else 0.0)

    # ── Volume check ───────────────────────────────────────────────
    V_medium_required_m3 = p["m_medium_kg"] / p["rho_bulk_kg_m3"]
    fill_fraction = (V_medium_required_m3 / V_vessel_m3
                     if V_vessel_m3 > 0 else 999.0)

    # ── Validation checks ──────────────────────────────────────────
    checks = [
        ("U-value (W/m²·K)",           U_wall_W_m2K,              "< 0.10",
         U_wall_W_m2K < 0.10),
        ("Self-discharge (%/h)",        self_discharge_pct_per_h,  "< 0.42",
         self_discharge_pct_per_h < 0.42),
        ("SOC after 12 h standby",      SOC_after_12h,             "> 0.95",
         SOC_after_12h > 0.95),
        ("Discharge duration (h)",      t_discharge_h,             "> 4.0",
         t_discharge_h > 4.0),
        ("T_hot below sand limit (K)",  p["T_hot_K"],              "< 1273",
         p["T_hot_K"] < 1273.0),
        ("Vessel fill fraction",        fill_fraction,             "< 0.85",
         fill_fraction < 0.85),
        ("Energy capacity (kWh)",       E_capacity_kWh,            "> 1.0",
         E_capacity_kWh > 1.0),
    ]

    return {
        # Interface outputs (project CLAUDE.md)
        "T_storage_hot_K":          p["T_hot_K"],
        "T_storage_cold_K":         p["T_cold_K"],
        "q_discharge_W":            p["q_discharge_W"],
        "E_stored_kWh":             E_capacity_kWh,
        "SOC":                      SOC_after_12h,

        # Capacity
        "E_capacity_kWh":           E_capacity_kWh,
        "E_capacity_J":             E_capacity_J,
        "E_usable_kWh":             E_usable_J / 3_600_000.0,
        "cp_avg_J_kgK":             cp_avg,

        # Losses
        "UA_total_W_K":             UA_total,
        "U_wall_W_m2K":             U_wall_W_m2K,
        "Q_loss_standby_W":         Q_loss_standby_W,
        "self_discharge_pct_per_h": self_discharge_pct_per_h,
        "SOC_after_12h":            SOC_after_12h,

        # Discharge
        "t_discharge_h":            t_discharge_h,

        # Geometry
        "V_vessel_m3":              V_vessel_m3,
        "H_vessel_m":               H,
        "A_outer_total_m2":         A_outer_total_m2,
        "fill_fraction":            fill_fraction,

        # Validation
        "checks":        checks,
        "checks_passed": sum(1 for *_, ok in checks if ok),
        "checks_total":  len(checks),
    }


def print_report(params=None):
    """Run evaluate() and print a formatted validation report."""
    p = {**DEFAULTS, **(params or {})}
    r = evaluate(p)

    print("=" * 70)
    print("THERMAL STORAGE (SAND BATTERY) — DESIGN VALIDATION")
    print("=" * 70)

    print("\n── VESSEL GEOMETRY ──")
    print(f"  Inner diameter:       {p['D_vessel_m']*1000:.0f} mm")
    print(f"  Aspect ratio H/D:     {p['AR_vessel']:.2f}")
    print(f"  Height:               {r['H_vessel_m']*1000:.0f} mm")
    print(f"  Inner volume:         {r['V_vessel_m3']*1000:.1f} L"
          f"  ({r['V_vessel_m3']:.3f} m³)")
    print(f"  Outer surface area:   {r['A_outer_total_m2']:.3f} m²")

    print("\n── STORAGE MEDIUM ──")
    print(f"  Medium mass:          {p['m_medium_kg']:.0f} kg")
    print(f"  Bulk density:         {p['rho_bulk_kg_m3']:.0f} kg/m³")
    print(f"  Fill fraction:        {r['fill_fraction']*100:.0f}%")
    print(f"  c_p average:          {r['cp_avg_J_kgK']:.0f} J/kg·K")
    print(f"  Temperature range:    {p['T_cold_K']-273.15:.0f}–{p['T_hot_K']-273.15:.0f}°C")
    print(f"  Energy capacity:      {r['E_capacity_kWh']:.2f} kWh"
          f"  ({r['E_capacity_J']/1e6:.2f} MJ)")

    print("\n── INSULATION ──")
    print(f"  Thickness:            {p['t_insulation_m']*1000:.0f} mm")
    print(f"  Conductivity:         {p['k_insulation_W_mK']:.4f} W/m·K")
    print(f"  UA_total:             {r['UA_total_W_K']:.3f} W/K")
    print(f"  U_wall:               {r['U_wall_W_m2K']:.4f} W/m²·K"
          f"  (target < 0.10)")

    print("\n── STANDBY LOSSES ──")
    print(f"  Q_loss at T_hot:      {r['Q_loss_standby_W']:.1f} W")
    print(f"  Self-discharge:       {r['self_discharge_pct_per_h']:.3f} %/h")
    print(f"  SOC after 12 h:       {r['SOC_after_12h']*100:.1f}%"
          f"  (target > 95%)")

    print("\n── DISCHARGE ──")
    print(f"  Rated discharge:      {p['q_discharge_W']:.0f} W")
    print(f"  Discharge duration:   {r['t_discharge_h']:.1f} h"
          f"  (target > 4 h)")
    print(f"  Usable energy:        {r['E_usable_kWh']:.2f} kWh")

    print("\n" + "=" * 70)
    print("VALIDATION CHECKS")
    print("=" * 70)
    for name, value, target, ok in r["checks"]:
        status = "PASS" if ok else "FAIL"
        val_str = f"{value:.4f}" if isinstance(value, float) else str(value)
        print(f"  [{status}]  {name:30s}  {val_str:>10s}  (target: {target})")
    print(f"\n  {r['checks_passed']}/{r['checks_total']} checks passed")
    return r


if __name__ == "__main__":
    print_report()
