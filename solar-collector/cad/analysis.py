"""
Parabolic Dish Solar Collector — Thermodynamic Model

Computes net thermal power delivered to the receiver from first-principles
optical and thermal loss mechanisms, suitable for design optimisation.

Physics modeled:
1. Intercept factor — Gaussian focal spot from combined tracking, mirror, and
   sun-shape angular errors; fraction captured by receiver aperture
2. Optical efficiency — mirror reflectivity, surface cleanliness, structural shading
3. Cavity effective emissivity — aperture-to-inner-area ratio amplifies wall emissivity
4. Radiation loss — through aperture (Stefan-Boltzmann, cavity model)
5. Convection loss — through aperture (natural + wind-driven)

Interface outputs (project CLAUDE.md):
  q_collector_W   Net thermal power delivered to thermal storage [W]
  T_focal_K       Focal point / receiver temperature [K]
  eta_collector   Overall collector efficiency (q / Q_solar) [–]

References:
- Duffie & Beckman, "Solar Engineering of Thermal Processes" (4th ed.), ch. 7
- Stine & Harrigan, "Solar Energy Fundamentals and Design" (1985), ch. 8
- Steinfeld & Schubnell, "Optimum aperture size and operating temperature of
  a solar cavity-receiver", Solar Energy 50 (1993) 19-25
"""

import math

# ── Physical constants ─────────────────────────────────────────────

SIGMA = 5.6704e-8   # Stefan-Boltzmann constant [W/m²·K⁴]

# ── Default design parameters ──────────────────────────────────────

DEFAULTS = {
    # Dish geometry
    "D_aperture_m":            1.00,   # aperture diameter [m]
    "focal_ratio":             0.60,   # focal length / aperture diameter [–]

    # Receiver geometry
    "D_aperture_receiver_m":   0.040,  # receiver aperture (opening) diameter [m]
    "D_cavity_m":              0.070,  # cavity inner diameter [m]
    "L_cavity_m":              0.060,  # cavity depth [m]

    # Receiver thermal
    "epsilon_receiver":        0.15,   # cavity wall emissivity [–]
    "T_receiver_K":            873.15, # target receiver temperature [K] (600°C)
    "h_conv_W_m2K":            10.0,   # convective HTC at aperture [W/m²·K]

    # Optical
    "rho_mirror":              0.92,   # mirror reflectivity (MIRO-SUN sheet) [–]
    "cleanliness":             0.95,   # mirror cleanliness factor [–]
    "f_shading":               0.02,   # structural shading fraction [–]

    # Angular error budget
    "sigma_tracking_mrad":     3.0,    # 1σ tracking error [mrad]
    "sigma_mirror_mrad":       2.5,    # 1σ mirror slope error (faceting) [mrad]
    "sigma_sun_mrad":          2.73,   # sun disk 1σ angular radius [mrad]
                                       # (4.65 mrad half-angle / sqrt(3) ≈ 2.73)

    # Operating conditions
    "DNI_W_m2":                850.0,  # direct normal irradiance [W/m²]
    "T_amb_K":                 298.15, # ambient temperature [K] (25°C)
}


def evaluate(params=None):
    """Evaluate collector performance from first-principles optical and thermal losses.

    The efficiency emerges from the physics — no fixed fraction of DNI assumed.

    Args:
        params: dict of design parameters (missing keys use DEFAULTS)

    Returns:
        dict with all computed metrics and validation checks
    """
    p = {**DEFAULTS, **(params or {})}

    # ── Dish geometry ──────────────────────────────────────────────
    A_aperture_m2 = math.pi / 4 * p["D_aperture_m"]**2    # aperture area [m²]
    f_m = p["focal_ratio"] * p["D_aperture_m"]             # focal length [m]

    # Rim angle of paraboloid: angle from optical axis to dish rim at focal point
    # tan(phi) = (D/2) / (f - (D/2)²/(4f))  — exact paraboloid geometry
    r_rim = p["D_aperture_m"] / 2
    phi_rim_rad = math.atan2(r_rim, f_m - r_rim**2 / (4 * f_m))

    # ── Receiver geometry ──────────────────────────────────────────
    r_ap = p["D_aperture_receiver_m"] / 2
    A_aperture_recv_m2 = math.pi * r_ap**2                 # receiver aperture area [m²]

    # Cavity inner surface area (cylindrical wall + back wall)
    A_cavity_inner_m2 = (math.pi * p["D_cavity_m"] * p["L_cavity_m"] +
                         math.pi / 4 * p["D_cavity_m"]**2)

    # Concentration ratio C = dish area / receiver aperture area
    C = A_aperture_m2 / A_aperture_recv_m2

    # ── Intercept factor ───────────────────────────────────────────
    # The focused beam has a finite angular spread from three independent
    # Gaussian error sources. Combined 1σ total error (RSS):
    sigma_total_mrad = math.sqrt(
        p["sigma_tracking_mrad"]**2 +
        p["sigma_mirror_mrad"]**2 +
        p["sigma_sun_mrad"]**2
    )
    sigma_total_rad = sigma_total_mrad * 1e-3

    # 1σ focal spot radius at the receiver plane
    sigma_spot_m = f_m * sigma_total_rad

    # Intercept factor: fraction of concentrated flux captured by the receiver
    # aperture. For a 2D Gaussian intensity distribution, this is the CDF
    # within a circle of radius r_ap centred on the focal point:
    #   γ = 1 - exp(-r_ap² / (2σ²))
    gamma = 1.0 - math.exp(-r_ap**2 / (2.0 * sigma_spot_m**2))

    # ── Optical chain ──────────────────────────────────────────────
    Q_solar_W = p["DNI_W_m2"] * A_aperture_m2  # incident power on dish aperture [W]

    # Mirror reflectivity × cleanliness × (1 - structural shading)
    eta_optical = p["rho_mirror"] * p["cleanliness"] * (1.0 - p["f_shading"])

    # Power arriving at receiver aperture plane (after optics and interception)
    Q_concentrated_W = Q_solar_W * eta_optical * gamma

    # ── Cavity effective emissivity ────────────────────────────────
    # A cavity receiver behaves as a near-blackbody because radiation bouncing
    # inside the cavity has multiple absorption chances before escaping.
    # Ref: Duffie & Beckman eq. 7.4.2 (cavity with aperture)
    #   ε_eff = 1 / (1 + (1/ε_wall - 1) × (A_aperture / A_inner))
    epsilon_eff = 1.0 / (
        1.0 + (1.0 / p["epsilon_receiver"] - 1.0) *
        (A_aperture_recv_m2 / A_cavity_inner_m2)
    )

    # ── Receiver thermal losses ────────────────────────────────────
    T_sky_K = p["T_amb_K"] - 20.0   # sky temperature ~20 K below ambient

    # Radiation loss through aperture (loss area = aperture, not full cavity wall)
    Q_loss_rad_W = (epsilon_eff * SIGMA * A_aperture_recv_m2 *
                    (p["T_receiver_K"]**4 - T_sky_K**4))

    # Natural + wind-driven convection loss through aperture opening
    Q_loss_conv_W = (p["h_conv_W_m2K"] * A_aperture_recv_m2 *
                     (p["T_receiver_K"] - p["T_amb_K"]))

    Q_loss_W = Q_loss_rad_W + Q_loss_conv_W

    # ── Net output ─────────────────────────────────────────────────
    q_collector_W = max(0.0, Q_concentrated_W - Q_loss_W)
    eta_collector = q_collector_W / Q_solar_W if Q_solar_W > 0 else 0.0
    Q_loss_frac = Q_loss_W / Q_solar_W if Q_solar_W > 0 else 1.0

    # ── Validation checks ──────────────────────────────────────────
    D_L_ratio = p["D_cavity_m"] / p["L_cavity_m"]
    ap_cavity_ratio = p["D_aperture_receiver_m"] / p["D_cavity_m"]

    checks = [
        ("Concentration ratio C",      C,              "> 500",
         C > 500),
        ("Intercept factor γ",         gamma,          "> 0.90",
         gamma > 0.90),
        ("Heat loss fraction",         Q_loss_frac,    "< 0.15",
         Q_loss_frac < 0.15),
        ("Net power q_coll (W)",       q_collector_W,  "> 400",
         q_collector_W > 400),
        ("Optical efficiency η_opt",   eta_optical,    "0.80-0.92",
         0.80 <= eta_optical <= 0.92),
        ("Cavity aspect D/L",          D_L_ratio,      "0.5-2.0",
         0.5 <= D_L_ratio <= 2.0),
        ("Aperture fits in cavity",    ap_cavity_ratio, "< 0.80",
         ap_cavity_ratio < 0.80),
    ]

    return {
        # Interface outputs (project CLAUDE.md)
        "q_collector_W":         q_collector_W,
        "T_focal_K":             p["T_receiver_K"],
        "eta_collector":         eta_collector,

        # Optical chain
        "Q_solar_W":             Q_solar_W,
        "Q_concentrated_W":      Q_concentrated_W,
        "eta_optical":           eta_optical,
        "gamma":                 gamma,
        "C":                     C,

        # Thermal losses
        "Q_loss_W":              Q_loss_W,
        "Q_loss_rad_W":          Q_loss_rad_W,
        "Q_loss_conv_W":         Q_loss_conv_W,
        "Q_loss_frac":           Q_loss_frac,
        "epsilon_eff":           epsilon_eff,

        # Geometry
        "A_aperture_m2":         A_aperture_m2,
        "A_aperture_recv_m2":    A_aperture_recv_m2,
        "f_m":                   f_m,
        "phi_rim_deg":           math.degrees(phi_rim_rad),
        "sigma_total_mrad":      sigma_total_mrad,
        "sigma_spot_m":          sigma_spot_m,

        # Validation
        "checks":         checks,
        "checks_passed":  sum(1 for *_, ok in checks if ok),
        "checks_total":   len(checks),
    }


def print_report(params=None):
    """Run evaluate() and print a formatted validation report."""
    p = {**DEFAULTS, **(params or {})}
    r = evaluate(p)

    print("=" * 70)
    print("PARABOLIC DISH COLLECTOR — DESIGN VALIDATION")
    print("=" * 70)

    print("\n── DISH GEOMETRY ──")
    print(f"  Aperture diameter:    {p['D_aperture_m']*1000:.0f} mm"
          f"  ({r['A_aperture_m2']:.3f} m²)")
    print(f"  Focal length:         {r['f_m']*1000:.0f} mm"
          f"  (f/D = {p['focal_ratio']:.2f})")
    print(f"  Rim angle:            {r['phi_rim_deg']:.1f}°")
    print(f"  Concentration ratio:  {r['C']:.0f}:1")

    print("\n── OPTICAL MODEL ──")
    print(f"  DNI:                  {p['DNI_W_m2']:.0f} W/m²")
    print(f"  Q_solar:              {r['Q_solar_W']:.1f} W")
    print(f"  Mirror reflectivity:  {p['rho_mirror']:.3f}")
    print(f"  Cleanliness:          {p['cleanliness']:.3f}")
    print(f"  Structural shading:   {p['f_shading']*100:.1f}%")
    print(f"  η_optical:            {r['eta_optical']*100:.1f}%")
    print(f"  Tracking 1σ:          {p['sigma_tracking_mrad']:.1f} mrad")
    print(f"  Mirror slope 1σ:      {p['sigma_mirror_mrad']:.1f} mrad")
    print(f"  Sun shape 1σ:         {p['sigma_sun_mrad']:.2f} mrad")
    print(f"  Combined σ_total:     {r['sigma_total_mrad']:.1f} mrad")
    print(f"  Focal spot 1σ radius: {r['sigma_spot_m']*1000:.1f} mm")
    print(f"  Receiver aperture:    ⌀{p['D_aperture_receiver_m']*1000:.1f} mm")
    print(f"  Intercept factor γ:   {r['gamma']*100:.1f}%")
    print(f"  Q_concentrated:       {r['Q_concentrated_W']:.1f} W")

    print("\n── RECEIVER THERMAL LOSSES ──")
    print(f"  Receiver temperature: {p['T_receiver_K'] - 273.15:.0f}°C"
          f"  ({p['T_receiver_K']:.1f} K)")
    print(f"  Cavity ε_wall:        {p['epsilon_receiver']:.3f}")
    print(f"  Cavity ε_effective:   {r['epsilon_eff']:.3f}")
    loss_pct = r["Q_loss_W"] / r["Q_solar_W"] * 100 if r["Q_solar_W"] > 0 else 0
    rad_pct  = r["Q_loss_rad_W"] / r["Q_solar_W"] * 100 if r["Q_solar_W"] > 0 else 0
    conv_pct = r["Q_loss_conv_W"] / r["Q_solar_W"] * 100 if r["Q_solar_W"] > 0 else 0
    print(f"  Q_loss radiation:     {r['Q_loss_rad_W']:.1f} W  ({rad_pct:.1f}% of Q_solar)")
    print(f"  Q_loss convection:    {r['Q_loss_conv_W']:.1f} W  ({conv_pct:.1f}% of Q_solar)")
    print(f"  Q_loss total:         {r['Q_loss_W']:.1f} W  ({loss_pct:.1f}% of Q_solar)")

    print("\n── NET OUTPUT ──")
    print(f"  q_collector_W:        {r['q_collector_W']:.1f} W")
    print(f"  η_collector:          {r['eta_collector']*100:.1f}%")

    print("\n" + "=" * 70)
    print("VALIDATION CHECKS")
    print("=" * 70)
    for name, value, target, ok in r["checks"]:
        status = "PASS" if ok else "FAIL"
        val_str = f"{value:.3f}" if isinstance(value, float) else str(value)
        print(f"  [{status}]  {name:30s}  {val_str:>10s}  (target: {target})")
    print(f"\n  {r['checks_passed']}/{r['checks_total']} checks passed")
    return r


if __name__ == "__main__":
    print_report()
