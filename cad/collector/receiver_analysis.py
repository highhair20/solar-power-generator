"""
Cavity Receiver — First-Principles Thermal Loss Model

Computes the net thermal output of a cavity receiver from first principles,
replacing the fixed "83% receiver efficiency" assumption in efficiency-targets.md.

Loss mechanisms modeled:
1. Radiation loss    — thermal emission from the aperture (Stefan-Boltzmann)
2. Convection loss   — natural + wind-forced convection from the hot cavity
3. Conduction loss   — through insulation to the environment

Also models:
- Effective emissivity of the cavity aperture
- Natural convection correlation for downward-facing hot aperture
- Wind convection from Siebers et al. (1984) SAND84-0483

References:
- Stine & McDonald (1989) "Cavity Receiver Heat Loss Measurements"
  ASME J. Solar Energy Engineering, 111(4)
- Leibfried & Ortjohann (1995) "Convective Heat Loss from Upward and
  Downward-Facing Cavity Solar Receivers"
- Siebers & Kraabel (1984) "Estimating Convective Energy Losses from
  Solar Central Receivers" SAND84-8717
"""

import math


STEFAN_BOLTZMANN = 5.67e-8  # W/(m²·K⁴)


DEFAULTS = {
    # Receiver geometry
    "aperture_diameter": 0.06,       # m — aperture opening (where concentrated flux enters)
    "cavity_diameter": 0.08,         # m — inner cavity diameter
    "cavity_depth": 0.10,            # m — cavity depth (absorber-to-aperture distance)

    # Temperatures
    "T_receiver": 600 + 273.15,      # K — cavity wall / absorber temperature
    "T_ambient": 25 + 273.15,        # K — ambient air temperature

    # Solar input
    "Q_solar_in": 550.0,             # W — concentrated flux from dish
    "dish_concentration": 1000.0,    # suns — geometric concentration ratio

    # ── Fix 1: Separate solar absorptance from thermal emissivity ──────
    # A selective absorber coating behaves very differently across the spectrum:
    #   - Solar wavelengths (0.3–2.5 μm): high absorptance captures incoming flux
    #   - Thermal wavelengths (2.5–25 μm): low emissivity limits re-emission loss
    #
    # Pyromark 2500 (high-temp black paint): α_solar≈0.95, ε_thermal≈0.87
    # Cermet selective coating (Mo-Al₂O₃):  α_solar≈0.96, ε_thermal≈0.05–0.15
    # Using α_solar for Q_absorbed and ε_thermal for Q_rad gives a realistic model.
    # The old single "absorptance" field is kept as a fallback alias.
    "absorptance_solar": 0.95,       # absorptance at solar wavelengths (Pyromark: ~0.95)
    "emissivity_thermal": 0.85,      # emissivity at thermal wavelengths (Pyromark: ~0.87)
                                     # For cermet selective coating use ε ≈ 0.10
    "aperture_emissivity_eff": None, # effective aperture emissivity — computed if None

    # ── Fix 4: Aperture window (quartz glass) ──────────────────────────
    # A quartz window over the aperture:
    #   + Eliminates aperture convection loss (seals cavity from wind/buoyancy)
    #   + Transmits ~93% of solar flux (quartz is transparent at solar wavelengths)
    #   - Absorbs ~70% of cavity thermal emission (quartz opaque at λ > 3.5 μm)
    # Tradeoff: convection loss eliminated, but radiation loss modestly increased.
    # Recommended for high-wind or high-tilt (near-horizontal) installations.
    "has_aperture_window": False,    # True = quartz window covers the aperture
    "window_solar_transmittance": 0.93,   # quartz: ~93% solar transmittance
    "window_thermal_transmittance": 0.30, # quartz: ~30% IR transmittance (opaque λ>3.5μm)

    # Insulation
    "insulation_thickness": 0.05,    # m — ceramic wool / alumina blanket
    "insulation_k": 0.15,            # W/(m·K) — high-temp mineral wool at mean temp
    "insulation_area": 0.04,         # m² — external surface area of insulated shell

    # Environment
    "wind_speed": 2.0,               # m/s — typical low-wind condition
    "receiver_tilt": 90.0,           # degrees from horizontal — 90° = horizontal aperture
                                     # facing down (dish pointed at zenith)
                                     # 0° = aperture facing up (horizontal)
}


def cavity_emissivity(aperture_area, cavity_area, surface_emissivity):
    """Compute effective emissivity of a cavity aperture.

    A cavity acts as a near-perfect blackbody because photons reflecting off
    the inner surface have multiple chances to be absorbed before escaping.

    Using the cavity factor formula (Stine & McDonald, 1989):
        ε_eff = 1 / (1 + (1/ε_s - 1) × A_aperture / A_cavity)

    where:
        ε_s    = surface emissivity
        A_ap   = aperture area
        A_cav  = total inner cavity surface area

    Args:
        aperture_area: m² — aperture opening area
        cavity_area: m² — total inner surface area of cavity
        surface_emissivity: surface emissivity of cavity coating

    Returns:
        Effective emissivity of aperture (0–1)
    """
    if cavity_area <= 0 or surface_emissivity <= 0:
        return surface_emissivity
    ratio = aperture_area / cavity_area
    eps_eff = 1.0 / (1.0 + (1.0 / surface_emissivity - 1.0) * ratio)
    return min(eps_eff, 1.0)


def natural_convection_loss(T_receiver, T_ambient, aperture_diameter, tilt_deg):
    """Compute natural convection heat loss from a cavity receiver aperture.

    Uses Leibfried & Ortjohann (1995) correlation for inclined receiver:
        Nu = C × (Gr × Pr)^n × (cos θ)^m
    where θ is the tilt from horizontal (0° = aperture up, 90° = sideways).

    For downward-facing aperture (dish at zenith, θ near 90°), natural
    convection is strongly suppressed — hot air stratifies inside the cavity.

    Args:
        T_receiver: K — receiver temperature
        T_ambient: K — ambient temperature
        aperture_diameter: m — aperture diameter
        tilt_deg: degrees from horizontal (0° = up, 90° = sideways, 180° = down)

    Returns:
        Q_conv_natural: W — natural convection heat loss
        h_natural: W/(m²·K) — convection coefficient
    """
    T_film = (T_receiver + T_ambient) / 2  # film temperature for air properties

    # Air properties at film temperature (ideal gas, power-law correlations)
    # Viscosity: Sutherland's law (Incropera et al. ref [13], Table A.4):
    #   μ = μ_ref × (T/T_ref)^1.5 × (T_ref + S) / (T + S)
    #   μ_ref = 1.716×10⁻⁵ Pa·s at T_ref = 273.15 K; Sutherland constant S = 110.4 K
    mu_air = 1.716e-5 * (T_film / 273.15)**1.5 * (273.15 + 110.4) / (T_film + 110.4)
    # Thermal conductivity: power-law fit to NIST air data (Incropera et al.):
    #   k = k_ref × (T/T_ref)^0.82,  k_ref = 0.0241 W/(m·K) at 273.15 K
    k_air = 0.0241 * (T_film / 273.15)**0.82
    # Specific heat: cp ≈ 1005 J/(kg·K) is nearly constant for air from 250–800 K
    # (varies < 5% over this range; Incropera et al. Table A.4)
    cp_air = 1005.0  # J/(kg·K)
    # Density from ideal gas law: ρ = P / (R_specific × T)
    # P = 101325 Pa (sea level); R_specific = R_universal/M_air = 8.314/0.02897 = 286.9 J/(kg·K)
    rho_air = 101325 / (287.0 * T_film)
    # Prandtl number
    Pr_air = mu_air * cp_air / k_air
    # Thermal expansion coefficient for ideal gas: β = 1/T (K⁻¹)
    beta = 1.0 / T_film  # K⁻¹

    g = 9.81  # m/s² — standard gravity (CODATA 2018: 9.80665 m/s²; 9.81 sufficient here)
    dT = max(T_receiver - T_ambient, 0)
    L = aperture_diameter  # characteristic length

    Gr = rho_air**2 * g * beta * dT * L**3 / mu_air**2
    Gr_Pr = Gr * Pr_air

    # Leibfried & Ortjohann correlation for cylindrical cavity:
    # For 0° < θ < 90° (aperture tilted toward horizontal or facing down):
    #   Nu = 0.088 × (Gr × Pr)^(1/3) × (T_receiver / T_ambient)^0.18 × (cos θ)^2.47
    # This captures the strong suppression of convection as aperture tilts downward.
    tilt_rad = math.radians(min(max(tilt_deg, 0), 180))
    cos_tilt = abs(math.cos(tilt_rad))  # |cos(90°)| = 0 → aperture sideways

    if Gr_Pr > 0:
        # Leibfried & Ortjohann (1995) eq. (7), valid for Gr·Pr > 10⁵:
        #   Nu = 0.088 × (Gr·Pr)^(1/3) × (T_h/T_a)^0.18 × (cos θ)^2.47
        # Coefficients 0.088, exponents 1/3, 0.18, and 2.47 are from regression
        # fits to calorimetric measurements on 60°–120° (parabolic-dish range)
        # cylindrical cavity receivers.
        # The (cos θ)^2.47 term captures the rapid convection suppression as the
        # aperture tilts below horizontal: at θ = 90° (sideways), cos θ = 0 →
        # Nu = 0, which is physically correct (hot air trapped in cavity).
        Nu = (0.088 * max(Gr_Pr, 1e5)**(1/3) *
              (T_receiver / T_ambient)**0.18 *
              cos_tilt**2.47)
        Nu = max(Nu, 0.1)  # floor: even perfectly downward receivers have some conduction loss
    else:
        Nu = 0.1

    h_natural = Nu * k_air / L
    A_aperture = math.pi / 4 * aperture_diameter**2
    Q_conv_natural = h_natural * A_aperture * dT

    return Q_conv_natural, h_natural


def wind_convection_loss(T_receiver, T_ambient, aperture_diameter, wind_speed):
    """Compute wind-forced convection heat loss from the receiver aperture.

    Uses the Siebers & Kraabel (1984) correlation for wind-forced convection
    on a heated surface (SAND84-8717):
        Nu_wind = 0.56 × Re^0.5  for Re < 3×10^5 (laminar-transitional)
        Nu_wind = 0.19 × Re^0.6  for Re > 3×10^5 (turbulent)

    Args:
        T_receiver: K — receiver temperature
        T_ambient: K — ambient temperature
        aperture_diameter: m — aperture diameter (characteristic length)
        wind_speed: m/s — freestream wind speed

    Returns:
        Q_conv_wind: W — wind convection heat loss
        h_wind: W/(m²·K) — wind convection coefficient
    """
    T_film = (T_receiver + T_ambient) / 2
    mu_air = 1.716e-5 * (T_film / 273.15)**1.5 * (273.15 + 110.4) / (T_film + 110.4)
    k_air = 0.0241 * (T_film / 273.15)**0.82
    rho_air = 101325 / (287.0 * T_film)

    Re = rho_air * wind_speed * aperture_diameter / mu_air

    if Re < 3e5:
        Nu_wind = 0.56 * Re**0.5
    else:
        Nu_wind = 0.19 * Re**0.6

    h_wind = Nu_wind * k_air / aperture_diameter
    A_aperture = math.pi / 4 * aperture_diameter**2
    dT = max(T_receiver - T_ambient, 0)
    Q_conv_wind = h_wind * A_aperture * dT

    return Q_conv_wind, h_wind


def evaluate(params=None):
    """Compute cavity receiver thermal losses from first principles.

    Args:
        params: dict of design parameters (missing keys use DEFAULTS)

    Returns:
        dict with all computed metrics including individual losses and net output
    """
    p = {**DEFAULTS, **(params or {})}

    T_h = p["T_receiver"]
    T_a = p["T_ambient"]
    d_ap = p["aperture_diameter"]
    d_cav = p["cavity_diameter"]
    depth = p["cavity_depth"]

    A_aperture = math.pi / 4 * d_ap**2

    # ── Cavity geometry ───────────────────────────────────────────
    # Inner cavity: cylindrical side wall + back wall
    A_cylinder = math.pi * d_cav * depth
    A_back = math.pi / 4 * d_cav**2
    A_cavity_total = A_cylinder + A_back  # total inner absorbing surface

    # ── Fix 1: Resolve absorptance/emissivity from new or old field names ─
    # New preferred fields: absorptance_solar, emissivity_thermal
    # Legacy fallback: absorptance / emissivity (for backward compatibility)
    alpha_solar = p.get("absorptance_solar") or p.get("absorptance", 0.95)
    eps_thermal = p.get("emissivity_thermal") or p.get("emissivity", 0.85)

    # ── Effective aperture emissivity (cavity factor) ─────────────
    # Uses ε_thermal (not α_solar): the cavity re-emits at thermal wavelengths.
    eps_eff = p.get("aperture_emissivity_eff") or cavity_emissivity(
        A_aperture, A_cavity_total, eps_thermal
    )

    # ── Fix 4: Quartz window — modify solar input and radiation loss ──────
    # When a quartz window is present:
    #   - Only τ_solar fraction of incoming solar flux enters the cavity.
    #   - Radiation emitted through the aperture is further attenuated by τ_thermal
    #     (quartz absorbs ~70% of thermal IR, reducing effective Q_rad loss).
    #   - Convection through the aperture is eliminated (cavity sealed from air).
    has_window = p.get("has_aperture_window", False)
    tau_solar = p.get("window_solar_transmittance", 0.93)
    tau_thermal = p.get("window_thermal_transmittance", 0.30)

    # Effective solar flux entering the cavity
    Q_solar_entering = p["Q_solar_in"] * (tau_solar if has_window else 1.0)

    # ── Loss 1: Radiation from aperture ──────────────────────────
    # Hot cavity emits radiation outward through the aperture.
    # Q_rad = ε_eff × σ × (T_receiver⁴ - T_ambient⁴) × A_aperture
    # With window: multiply by τ_thermal (window partially blocks thermal emission).
    Q_rad_bare = eps_eff * STEFAN_BOLTZMANN * (T_h**4 - T_a**4) * A_aperture
    Q_rad = Q_rad_bare * (tau_thermal if has_window else 1.0)

    # ── Loss 2: Natural convection ────────────────────────────────
    # With a sealed window: no aperture convection.
    if has_window:
        Q_conv_nat = 0.0
        h_nat = 0.0
    else:
        Q_conv_nat, h_nat = natural_convection_loss(T_h, T_a, d_ap, p["receiver_tilt"])

    # ── Loss 3: Wind convection ───────────────────────────────────
    # With a sealed window: no wind-driven aperture convection.
    if has_window:
        Q_conv_wind = 0.0
        h_wind = 0.0
    else:
        Q_conv_wind, h_wind = wind_convection_loss(T_h, T_a, d_ap, p["wind_speed"])

    # Take the larger of natural and wind convection.
    # Siebers & Kraabel (1984) SAND84-8717 §3 note that natural and forced
    # convection do NOT add linearly at the aperture: whichever creates the
    # thicker thermal boundary layer dominates and suppresses the other.
    # Using max() is the conservative (higher-loss) estimate; a full
    # mixed-convection correlation (e.g. Churchill 1977) would be more accurate
    # but is within ~10% of max() for this geometry.
    Q_conv = max(Q_conv_nat, Q_conv_wind)
    h_conv = max(h_nat, h_wind)

    # ── Loss 4: Conduction through insulation ─────────────────────
    Q_cond = (p["insulation_k"] * p["insulation_area"] *
              (T_h - T_a) / p["insulation_thickness"])

    # ── Total losses and net output ───────────────────────────────
    Q_loss_total = Q_rad + Q_conv + Q_cond
    Q_absorbed = Q_solar_entering * alpha_solar
    Q_net = max(0.0, Q_absorbed - Q_loss_total)

    eta_receiver = Q_net / p["Q_solar_in"] if p["Q_solar_in"] > 0 else 0.0

    return {
        "Q_solar_in": p["Q_solar_in"],
        "Q_solar_entering": Q_solar_entering,
        "Q_absorbed": Q_absorbed,
        "Q_rad": Q_rad,
        "Q_conv_natural": Q_conv_nat,
        "Q_conv_wind": Q_conv_wind,
        "Q_conv": Q_conv,
        "Q_cond": Q_cond,
        "Q_loss_total": Q_loss_total,
        "Q_net": Q_net,
        "eta_receiver": eta_receiver,
        "eps_eff_aperture": eps_eff,
        "h_conv": h_conv,
        "A_aperture_m2": A_aperture,
        "A_cavity_m2": A_cavity_total,
        "alpha_solar": alpha_solar,
        "emissivity_thermal": eps_thermal,
        "has_aperture_window": has_window,
    }


def print_report(params=None):
    """Run evaluate() and print a formatted report."""
    p = {**DEFAULTS, **(params or {})}
    r = evaluate(p)

    print("=" * 60)
    print("CAVITY RECEIVER — THERMAL LOSS ANALYSIS")
    print("=" * 60)

    print(f"\n  Aperture diameter:    {p['aperture_diameter']*1000:.0f} mm")
    print(f"  Cavity diameter:      {p['cavity_diameter']*1000:.0f} mm")
    print(f"  Cavity depth:         {p['cavity_depth']*1000:.0f} mm")
    print(f"  Receiver temperature: {p['T_receiver']-273.15:.0f} °C")
    print(f"  Ambient temperature:  {p['T_ambient']-273.15:.0f} °C")
    print(f"  Tilt from horizontal: {p['receiver_tilt']:.0f}°")
    print(f"  Wind speed:           {p['wind_speed']:.1f} m/s")
    print(f"  Absorptance (solar):  {r['alpha_solar']:.3f}")
    print(f"  Emissivity (thermal): {r['emissivity_thermal']:.3f}")
    print(f"  Eff. cavity emiss:    {r['eps_eff_aperture']:.3f}")
    window_str = (f"YES  (τ_solar={p['window_solar_transmittance']:.2f}, "
                  f"τ_thermal={p['window_thermal_transmittance']:.2f})"
                  if p.get('has_aperture_window') else "NO")
    print(f"  Aperture window:      {window_str}")

    print(f"\n── LOSS BUDGET ──")
    print(f"  Solar input:          {r['Q_solar_in']:.1f} W")
    if r['has_aperture_window']:
        print(f"  After window (τ={p['window_solar_transmittance']:.2f}): "
              f"{r['Q_solar_entering']:.1f} W")
    print(f"  Absorbed (×{r['alpha_solar']:.2f}):     {r['Q_absorbed']:.1f} W")
    print(f"")
    print(f"  Radiation loss:       {r['Q_rad']:>6.1f} W  "
          f"({r['Q_rad']/r['Q_solar_in']*100:.1f}%)")
    print(f"  Convection (nat):     {r['Q_conv_natural']:>6.1f} W  "
          f"({r['Q_conv_natural']/r['Q_solar_in']*100:.1f}%)")
    print(f"  Convection (wind):    {r['Q_conv_wind']:>6.1f} W  "
          f"({r['Q_conv_wind']/r['Q_solar_in']*100:.1f}%)")
    print(f"  Convection (used):    {r['Q_conv']:>6.1f} W  "
          f"(max of nat/wind)")
    print(f"  Conduction (insul):   {r['Q_cond']:>6.1f} W  "
          f"({r['Q_cond']/r['Q_solar_in']*100:.1f}%)")
    print(f"  ─────────────────────────────")
    print(f"  Total losses:         {r['Q_loss_total']:>6.1f} W  "
          f"({r['Q_loss_total']/r['Q_solar_in']*100:.1f}%)")
    print(f"")
    print(f"  NET THERMAL OUTPUT:   {r['Q_net']:>6.1f} W")
    print(f"  RECEIVER EFFICIENCY:  {r['eta_receiver']*100:.1f}%")
    print("=" * 60)
    return r


if __name__ == "__main__":
    print_report()

    # Sensitivity: show how efficiency varies with aperture size
    print("\n── APERTURE SIZE SENSITIVITY ──")
    print(f"  {'d_ap (mm)':>10}  {'Q_rad (W)':>9}  {'Q_conv (W)':>10}  "
          f"{'Q_net (W)':>9}  {'η (%)':>6}")
    for d_mm in [40, 50, 60, 70, 80, 100]:
        r = evaluate({"aperture_diameter": d_mm / 1000})
        print(f"  {d_mm:>10}  {r['Q_rad']:>9.1f}  {r['Q_conv']:>10.1f}  "
              f"  {r['Q_net']:>9.1f}  {r['eta_receiver']*100:>6.1f}")
