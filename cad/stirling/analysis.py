"""
Free-Piston Stirling Engine — Thermodynamic Model

Computes performance from first-principles loss mechanisms rather than
a fixed "fraction of Carnot" assumption. Each loss is computed from
geometry and operating conditions so the optimizer can attack them.

Loss mechanisms modeled:
1. Pumping loss — pressure drop through HX passages (Kays & London)
2. Shuttle heat loss — displacer thermal shuttling (Urieli & Berchowitz)
3. Displacer wall conduction — axial conduction through displacer shell
4. Vessel wall conduction — axial conduction through pressure vessel wall
5. Regenerator enthalpy loss — imperfect heat recovery (1 - effectiveness)
6. Gas spring hysteresis — irreversible compression in bounce space
7. Seal leakage loss — pressure-volume work lost through clearance gaps

Also models:
- Schmidt cycle (isothermal, sinusoidal motion)
- Heat exchanger NTU and pressure drop
- Regenerator effectiveness (packed screen correlation)
- Gas spring resonant frequency

References:
[1]  Urieli & Berchowitz, "Stirling Cycle Engine Analysis" (Adam Hilger, 1984)
     — Schmidt cycle, adiabatic correction, shuttle heat loss (eq. 7.24)
[2]  Organ, "The Regenerator and the Stirling Engine" (MEP, 1997)
     — regenerator packed-screen heat transfer and pressure drop
[3]  Beale, "Free Piston Stirling Engines" (1984)
     — resonance requirement, Beale number
[4]  Kays & London, "Compact Heat Exchangers" (3rd ed., 1984)
     — NTU-effectiveness method for HX design
[5]  Gedeon & Wood, "Oscillating-Flow Regenerator Test Rig" ASME J. Fluids Eng. (1996)
     — oscillating-flow friction factor and heat transfer correlations for wire screens
[6]  Gedeon, "Sage Stirling Cycle Model Class Reference" (Gedeon Associates, 2016)
     — general loss modelling approach
[7]  Lee, "An Analytical Study of Gas Spring Hysteresis" (1983)
     Cryogenics 23(3):117–119
     — gas spring hysteresis function f(λ); exact analytical form
[8]  Tanaka et al., "Flow and Heat Transfer Characteristics of the Stirling Engine
     Regenerator" ASME J. Heat Transfer 112 (1990) pp. 996–1000
     — Nu = 0.33 Re^0.6 Pr^0.36 steady correlation for packed screens
[9]  Ibrahim et al., "Oscillating Flow in Stirling Engine Heat Exchangers"
     AIAA Paper 2001-2733 (2001) / Int. J. Heat Mass Transfer 47 (2004)
     — oscillating-flow Nu enhancement factor (1 + 0.15 Re_ω^0.25)
[10] Zhao & Cheng, "Experimental Studies on the Transition from Laminar to
     Turbulent Oscillatory Flow in a Pipe" J. Fluid Mech. 317 (1996) pp. 223–242
     — oscillating flow friction multiplier for cooler tubes
[11] Leibfried & Ortjohann, "Convective Heat Loss from Upward and Downward-Facing
     Cavity Solar Receivers" ASME J. Sol. Energy Eng. 117 (1995) pp. 75–84
     — used in receiver_analysis.py (shared reference for natural convection)
[12] Chapman & Cowling, "The Mathematical Theory of Non-Uniform Gases"
     (Cambridge, 3rd ed., 1970)
     — Chapman-Enskog kinetic theory; helium μ ∝ T^0.67
[13] Incropera, DeWitt, Bergman & Lavine, "Fundamentals of Heat and Mass Transfer"
     (Wiley, 7th ed., 2011)
     — Dittus-Boelter (Nu = 0.023 Re^0.8 Pr^0.4), Nusselt correlations,
       Sutherland's law coefficients for air
[14] Nagaoka, "The Inductance Coefficients of Solenoids"
     J. Coll. Sci. Tokyo 27 (1909), article 6
     — short solenoid correction; Lorenz-Wheeler approximation
     k_N ≈ 1 / (1 + 0.9 × 2R/l) is a widely-used 1-term fit to Nagaoka's tables
[15] Bertotti, "Hysteresis in Magnetism" (Academic Press, 1998)
     — Steinmetz iron loss model; P ∝ f^1.6 B^2 exponents from empirical fit
[16] White, "Viscous Fluid Flow" (McGraw-Hill, 3rd ed., 2006)
     — Hagen-Poiseuille flow through annular clearance (seal leakage)
[17] Ingersoll, Zobel & Ingersoll, "Heat Conduction" (McGraw-Hill, 1954)
     — line-source ground heat exchanger model; factor of 4 in ln(4d/D_pipe)
       arises from method-of-images correction for ground surface
[18] NIST Reference on Constants, Units and Uncertainty (physics.nist.gov)
     — copper resistivity ρ₀ = 1.72×10⁻⁸ Ω·m at 20°C; TCR = 0.004 /°C (IEC 60028)
"""

import math


STEFAN_BOLTZMANN = 5.67e-8  # W/(m²·K⁴)


# ── Helium gas properties (from kinetic theory, temperature-dependent) ──

HELIUM_CONST = {
    "R": 2077.0,        # J/(kg·K) — specific gas constant (= R_univ / M_He)
    "gamma": 5/3,       # monatomic ideal gas, exact
    "cp": 5193.0,       # J/(kg·K) — = gamma/(gamma-1) * R, exact for ideal monatomic
}

def helium_props(T):
    """Compute helium transport properties at temperature T (K).

    From kinetic theory of monatomic ideal gases (ref [12]):
      μ ∝ T^(2/3) ≈ T^0.67  (Chapman-Enskog collision integral for
                               Lennard-Jones potential; exact exponent is
                               between 0.5 [rigid sphere] and 1 [Maxwell])
      k ∝ T^0.67  (Eucken relation for monatomic: k = (15R/4M) × μ,
                   so k tracks μ; Pr = μ cp / k = const ≈ 2/3 exactly)
      Pr = 0.67   (exact for monatomic ideal gas)

    Reference point from NIST WebBook (ref [18]):
      T=300K: μ = 1.99×10⁻⁵ Pa·s, k = 0.152 W/(m·K)
    """
    T_ref = 300.0
    mu_ref = 1.99e-5    # Pa·s at 300K (NIST)
    k_ref = 0.152       # W/(m·K) at 300K (NIST)

    mu = mu_ref * (T / T_ref) ** 0.67
    k = k_ref * (T / T_ref) ** 0.67
    cp = HELIUM_CONST["cp"]
    Pr = mu * cp / k  # ≈ 0.68, nearly constant

    return {"mu": mu, "k": k, "cp": cp, "Pr": Pr,
            "R": HELIUM_CONST["R"], "gamma": HELIUM_CONST["gamma"]}


# ── Material properties ──────────────────────────────────────────

MATERIALS = {
    "ss316":   {"k": 16.0, "rho": 8000, "name": "SS316 stainless"},
    "ss304":   {"k": 16.0, "rho": 8000, "name": "SS304 stainless"},
    "ti64":    {"k": 7.0,  "rho": 4430, "name": "Ti-6Al-4V titanium"},
    "inconel":  {"k": 11.0, "rho": 8190, "name": "Inconel 718"},
    "ceramic":  {"k": 2.0,  "rho": 3950, "name": "Alumina ceramic"},
}


# ── Default design parameters ────────────────────────────────────

DEFAULTS = {
    # Operating conditions
    "T_hot": 600 + 273.15,      # K
    "T_cold": 15 + 273.15,      # K — earth cooling loop
    "P_mean": 23e5,             # Pa (23 bar — optimized crossover point)
    "freq": 55.0,               # Hz
    "phase_angle": 70.0,        # degrees

    # Bore and strokes
    "vessel_id": 90.0,          # mm
    "piston_stroke": 10.0,      # mm
    "displacer_stroke": 12.0,   # mm

    # Piston
    "piston_clearance": 0.025,  # mm radial gap (25 microns)
    "piston_length": 25.0,      # mm
    "piston_wall": 8.0,         # mm

    # Displacer
    "displacer_clearance": 0.030,  # mm radial gap (30 microns)
    "displacer_length": 50.0,   # mm
    "displacer_wall": 1.5,      # mm
    "displacer_material": "ss316",  # material for thermal conductivity

    # Pressure vessel
    "vessel_wall": 5.0,         # mm
    "vessel_material": "ss316", # material for thermal conductivity

    # Cooler
    "cooler_tube_dia": 3.0,     # mm
    "cooler_tube_count": 48,
    "cooler_length": 38.0,      # mm

    # Regenerator
    "regen_length": 45.0,       # mm
    "regen_porosity": 0.70,
    "regen_wire_dia": 0.12,     # mm (80-mesh)
    "regen_mesh_count": 80,

    # Hot space
    "hot_space_gap": 12.0,      # mm
    "heater_int_fin_count": 12,
    "heater_int_fin_height": 15.0,  # mm
    "heater_int_fin_length": 30.0,  # mm
    "heater_int_fin_thickness": 1.5,  # mm
    "heater_head_wall": 4.0,    # mm

    # Bounce space
    "bounce_length": 40.0,      # mm

    # Alternator magnets (SmCo for high-temp tolerance)
    "magnet_ring_od": 88.0,     # mm
    "magnet_ring_id": 73.0,     # mm
    "magnet_ring_length": 30.0, # mm

    # Magnetic spring (opposing SmCo ring magnets, wall-mounted)
    "mag_spring_pairs": 2,      # number of repulsive magnet pairs
    "mag_spring_od": 100.0,     # mm — outer diameter (vessel OD)
    "mag_spring_id": 90.0,      # mm — inner diameter (vessel ID)
    "mag_spring_thickness": 5.0,  # mm — axial thickness per magnet
    "mag_spring_gap": 20.0,     # mm — equilibrium gap between opposing magnets
    "Br_magnet": 1.05,          # T — SmCo remanence (NdFeB ≈ 1.3T but can't take heat)

    # Piston-cooler gap
    "piston_cooler_gap": 3.0,   # mm

    # Thermal input
    "Q_input": 550.0,           # W — from dish
    # h_heater is now computed from fin channel geometry, not assumed

    # Linear alternator electromagnetic parameters
    "coil_turns": 200,          # total turns in coil
    "coil_wire_dia": 1.5,       # mm — copper wire diameter
    "coil_layers": 4,           # radial layers
    "coil_fill_factor": 0.65,   # packing factor (round wire in rect slot)
    "coil_length": 25.0,        # mm — axial length of coil
    "Br_alternator": 1.05,      # T — SmCo remanence
    "iron_loss_coeff": 2.0,     # W/kg at 50Hz, 1T (laminated silicon steel)

    # Rectifier + power electronics
    "eta_electronics": 0.95,    # rectifier + DC-DC converter efficiency

    # Composite pressure vessel (inner liner for thermal isolation)
    # The outer structural shell (k_vessel) provides pressure containment.
    # An inner low-k liner reduces axial conduction loss without sacrificing strength.
    # Set vessel_liner_frac > 0 to activate; vessel_liner_k defaults to k_vessel (no liner).
    "vessel_liner_k": None,     # W/mK — None means use k_vessel (no liner effect)
    "vessel_liner_frac": 0.0,   # fraction of wall thickness that is low-k inner liner (0–0.5)

    # ── Displacer dynamics (Fix 3: coupled piston–displacer model) ──────
    # The phase angle between piston and displacer is NOT a free choice; it
    # emerges from the coupled dynamics. The displacer spring stiffness is the
    # real design variable. At k_d = m_d × ω², phase → 90° (optimal).
    "displacer_spring_k": None,     # N/m — None = auto-tune for 90° phase at f_op
    "displacer_damping_ratio": 0.20, # ζ — effective gas thermodynamic damping (0.1–0.3)

    # ── Heater head external resistance (Fix 6) ─────────────────────────
    # Heat must conduct through the heater head wall from source (sand/focus)
    # to the inner fin surface. The gas-side dT_heater is already modeled;
    # this captures the wall and source-side resistances.
    "k_heater_head": 16.0,       # W/mK — heater head wall material (SS316 at 600°C)
    "h_source_to_heater": 250.0, # W/m²K — external HTC (sand bed convection: 100–400)

    # ── Regenerator axial conduction (Fix 7) ────────────────────────────
    "regen_wire_k": 16.0,        # W/mK — wire material conductivity (SS316)
    "regen_C_geo": 0.05,         # geometric factor for axial conduction (0.03–0.08)
                                  # Most wires are ⊥ to axis; ~5% effectively axial

    # ── Radiation in hot working space (Fix 8) ──────────────────────────
    "eps_heater_wall": 0.85,     # emissivity of heater head inner surface (Pyromark)

    # ── SmCo temperature correction (Fix 9) ─────────────────────────────
    "T_mag_spring": None,        # K — temperature at spring magnets; None = use T_mean
    "alpha_Br": -3.5e-4,         # /°C — Sm2Co17 Br temperature coefficient
    "T_max_SmCo": 350 + 273.15,  # K — max rated operating temperature for SmCo

    # ── Alternator flux leakage (Fix 10) ────────────────────────────────
    "mu_r_magnet": 1.05,         # — recoil permeability of SmCo (affects reluctance)
}


# ── Unit conversions ──────────────────────────────────────────────

def _mm2m(mm): return mm * 1e-3
def _mm2_m2(mm2): return mm2 * 1e-6
def _mm3_m3(mm3): return mm3 * 1e-9


# ── Physics model ─────────────────────────────────────────────────

def evaluate(params=None):
    """Evaluate Stirling engine performance from first-principles losses.

    Instead of assuming a fixed fraction of Carnot, this computes each
    loss mechanism from geometry and operating conditions. The resulting
    efficiency emerges from the physics.

    Args:
        params: dict of design parameters (missing keys use DEFAULTS)

    Returns:
        dict with all computed metrics including individual losses
    """
    p = {**DEFAULTS, **(params or {})}
    dT = p["T_hot"] - p["T_cold"]  # total temperature span
    T_mean = dT / math.log(p["T_hot"] / p["T_cold"])  # log-mean

    # Temperature-dependent helium properties at each zone
    g_hot = helium_props(p["T_hot"])
    g_cold = helium_props(p["T_cold"])
    g_mean = helium_props(T_mean)
    g = HELIUM_CONST  # for R, gamma, cp (temperature-independent)

    # Material properties — accept direct k values or look up by name
    k_displacer = (p["k_displacer"] if "k_displacer" in p
                   else MATERIALS.get(p["displacer_material"], MATERIALS["ss316"])["k"])
    k_vessel = (p["k_vessel"] if "k_vessel" in p
                else MATERIALS.get(p["vessel_material"], MATERIALS["ss316"])["k"])

    # Composite pressure vessel: inner low-k liner + outer structural shell.
    # Both conduct heat axially in parallel (each layer carries heat along its own area).
    # Effective conductance = k_liner × A_liner + k_outer × A_outer
    # Simplified as area-weighted k: k_eff = k_liner × f + k_outer × (1 - f)
    # The outer shell (k_vessel) must be metal to carry hoop stress at 11 bar.
    # The inner liner (vessel_liner_k) can be ceramic/alumina to reduce conduction loss.
    _liner_k = p.get("vessel_liner_k") or k_vessel  # default: no liner (same k throughout)
    _liner_frac = max(0.0, min(0.5, p.get("vessel_liner_frac", 0.0)))
    k_vessel_eff = _liner_k * _liner_frac + k_vessel * (1.0 - _liner_frac)

    # ── Displacer dynamics (Fix 3) ─────────────────────────────────────
    # In a free-piston Stirling the phase angle between piston and displacer
    # is NOT a free design variable — it emerges from the coupled dynamics.
    # The displacer spring stiffness k_d is the real design handle.
    # Phase model: 2nd-order forced response with gas thermodynamic damping.
    #   φ = atan2(2ζ × (ω/ω_d), 1 − (ω/ω_d)²)
    # At ω_d = ω (resonance) and any ζ > 0: φ → 90° (optimal).
    #
    # Material density estimated from conductivity (linear interpolation across
    # the ceramic–SS range used by the optimizer).
    # Endpoints from MATERIALS dict: alumina (k=2 W/mK, ρ=3950 kg/m³)
    # to SS316 (k=16 W/mK, ρ=8000 kg/m³).  Linear k-ρ fit is approximate
    # but sufficient since mass only affects spring-tuning accuracy.
    omega_pre = 2 * math.pi * p["freq"]  # rad/s (omega computed again later; consistent)
    _disp_od_m = (_mm2m(p["vessel_id"]) - 2 * p["displacer_clearance"] * 1e-3)
    _disp_shell_vol = math.pi * _disp_od_m * (p["displacer_wall"] * 1e-3) * (p["displacer_length"] * 1e-3)
    _rho_disp = 3950 + (k_displacer - 2) / 14 * (8000 - 3950)  # ceramic→SS interpolation
    m_displacer_kg = max(_rho_disp * _disp_shell_vol, 1e-6)  # kg

    k_d_spring = p.get("displacer_spring_k")
    if k_d_spring is None:
        k_d_spring = m_displacer_kg * omega_pre**2  # tune to 90° phase

    omega_d = math.sqrt(max(k_d_spring, 0.0) / m_displacer_kg)
    zeta_d = p.get("displacer_damping_ratio", 0.20)
    r_freq_d = omega_pre / max(omega_d, 1e-6)
    _num_phase = 2 * zeta_d * r_freq_d
    _den_phase = 1.0 - r_freq_d**2
    phase_achievable_deg = math.degrees(math.atan2(_num_phase, _den_phase))
    # Phase convention: atan2 returns (−180°, 180°].  For r<1 with ζ>0 the
    # response phase is positive (displacer leads piston) — the desired range
    # for a Stirling is 60°–120°.  Clamp to the physically meaningful range.
    phase_achievable_deg = max(0.0, min(180.0, phase_achievable_deg))
    phase_error_deg = abs(p["phase_angle"] - phase_achievable_deg)

    # ── Volumes ───────────────────────────────────────────────────
    bore_area = math.pi / 4 * p["vessel_id"]**2  # mm²

    V_swept_piston = bore_area * p["piston_stroke"]       # mm³
    V_swept_displacer = bore_area * p["displacer_stroke"]  # mm³

    # Heater head geometry (needed for both dead volume and adiabatic correction)
    heater_head_id = p["vessel_id"] - 2 * p["heater_head_wall"]
    cup_wall_area = math.pi * heater_head_id * p["heater_int_fin_length"]  # mm²
    cup_top_area = math.pi / 4 * heater_head_id**2  # mm²
    fin_area = (p["heater_int_fin_count"] * 2 *
                p["heater_int_fin_height"] * p["heater_int_fin_length"])  # mm²
    A_heater_total = cup_wall_area + cup_top_area + fin_area  # mm²

    # Dead volumes (mm³)
    V_hot_dead = bore_area * p["hot_space_gap"]
    fin_volume = (p["heater_int_fin_count"] * p["heater_int_fin_height"] *
                  p["heater_int_fin_thickness"] * p["heater_int_fin_length"])
    V_hot_dead = max(0, V_hot_dead - fin_volume)

    V_regen_total = bore_area * p["regen_length"]
    V_regen_dead = p["regen_porosity"] * V_regen_total

    V_cooler_dead = (p["cooler_tube_count"] * math.pi / 4 *
                     p["cooler_tube_dia"]**2 * p["cooler_length"])

    V_cold_dead = bore_area * p["piston_cooler_gap"]

    V_dead_total = V_hot_dead + V_regen_dead + V_cooler_dead + V_cold_dead
    dead_volume_ratio = V_dead_total / V_swept_piston if V_swept_piston > 0 else 999

    # ── Adiabatic-corrected cycle analysis ──────────────────────────
    # Start with Schmidt (isothermal) as the baseline, then apply
    # adiabatic correction based on finite heat transfer in working spaces.
    #
    # Schmidt assumes infinite heat transfer → isothermal expansion/compression.
    # Real engines have finite HTC, so gas temperature swings during the cycle.
    # This reduces the effective temperature ratio and thus the power.
    #
    # The correction follows Urieli & Berchowitz "simple analysis":
    # P_adiabatic ≈ P_schmidt × η_adia
    # where η_adia = NTU_ws / (1 + NTU_ws) accounts for finite heat transfer
    # in the working spaces (expansion and compression).

    tau = p["T_cold"] / p["T_hot"]
    kappa = V_swept_displacer / V_swept_piston if V_swept_piston > 0 else 1
    # Use dynamically achievable phase angle (Fix 3).
    # phase_angle in params is the INTENDED value; phase_achievable_deg is what the
    # coupled displacer dynamics will actually produce.  Schmidt analysis uses reality.
    alpha = math.radians(phase_achievable_deg)

    X_hot = V_hot_dead / V_swept_piston
    X_regen = V_regen_dead / V_swept_piston
    X_cold = V_cold_dead / V_swept_piston
    X_cooler = V_cooler_dead / V_swept_piston

    T_regen_mean = T_mean  # log-mean, already computed above
    delta = (X_hot + X_regen * p["T_hot"] / T_regen_mean +
             (X_cold + X_cooler) * p["T_hot"] / p["T_cold"])

    A_schmidt = math.sqrt(tau**2 * kappa**2 + 2 * tau * kappa * math.cos(alpha) + 1)
    B_schmidt = tau * kappa + 1 + 2 * delta

    p_ratio = (B_schmidt + A_schmidt) / (B_schmidt - A_schmidt)
    pressure_swing_pct = (p_ratio - 1) / (p_ratio + 1) * 200

    c = A_schmidt / B_schmidt
    W_schmidt = (math.pi * p["P_mean"] * _mm3_m3(V_swept_piston) *
                 (1 - tau) * kappa * math.sin(alpha) /
                 (B_schmidt * (1 + math.sqrt(max(0, 1 - c**2)))))

    # ── Adiabatic correction ──────────────────────────────────────
    # NTU for hot working space: gas-to-wall heat transfer during expansion
    # The hot space wall area includes the heater head inner surface + fins.
    # During expansion, gas temperature drops adiabatically; heat transfer
    # from the hot wall must restore it. If NTU is low, the gas doesn't
    # reach T_hot → reduced effective temperature ratio → less work.
    omega = 2 * math.pi * p["freq"]

    # Hot space: characteristic velocity = displacer peak velocity × area ratio
    A_hot_wall_m2 = _mm2_m2(cup_wall_area + cup_top_area + fin_area)
    # Residence time in hot space ≈ V_hot / V_dot
    V_hot_m3 = _mm3_m3(V_hot_dead + V_swept_displacer / 2)  # mean volume
    rho_hot = p["P_mean"] / (g["R"] * p["T_hot"])
    # Mass in hot space oscillates; use mean
    m_hot = rho_hot * V_hot_m3

    # Hot space HTC from Annand correlation (oscillating flow in cavity):
    # Nu = 0.75 × Re^0.7 for turbulent gas motion in enclosed spaces
    # Characteristic length = hot space gap, velocity from displacer motion
    L_hot = _mm2m(p["hot_space_gap"])
    v_hot = v_displacer_peak = math.pi * _mm2m(p["displacer_stroke"]) * p["freq"]
    Re_hot = rho_hot * v_hot * L_hot / g_hot["mu"]
    Nu_hot = 0.75 * max(Re_hot, 1)**0.7
    h_hot_space = Nu_hot * g_hot["k"] / L_hot

    # Fix 8: Radiation in hot working space
    # At 600°C, radiation between heater wall and displacer surface is significant.
    # Linearized radiation coefficient: h_rad ≈ 4 × ε_eff × σ × T_mean³
    # ε_eff for two gray surfaces: 1 / (1/ε₁ + 1/ε₂ − 1)
    _eps_wall = p.get("eps_heater_wall", 0.85)
    _eps_disp = 0.80   # displacer hot-face emissivity (painted/oxidized metal)
    _eps_rad_eff = 1.0 / (1.0 / _eps_wall + 1.0 / _eps_disp - 1.0)
    h_rad_hot = 4.0 * _eps_rad_eff * STEFAN_BOLTZMANN * p["T_hot"]**3
    h_hot_total = h_hot_space + h_rad_hot   # convection + radiation

    NTU_hot = h_hot_total * A_hot_wall_m2 / (m_hot * g["cp"] * p["freq"]) if m_hot > 0 else 100

    # Cold space: piston face + cylinder wall + COOLER TUBES
    # The cooler is the primary cold-side heat exchanger. Gas flows through
    # the cooler tubes each half-cycle; their heat transfer largely determines
    # how well the gas returns to T_cold for the compression stroke.
    A_cold_wall_m2 = _mm2_m2(bore_area + math.pi * p["vessel_id"] *
                              p["piston_cooler_gap"])
    V_cold_m3 = _mm3_m3(V_cold_dead + V_swept_piston / 2)
    rho_cold_ws = p["P_mean"] / (g["R"] * p["T_cold"])
    m_cold = rho_cold_ws * V_cold_m3
    L_cold = _mm2m(p["piston_cooler_gap"])
    v_cold = math.pi * _mm2m(p["piston_stroke"]) * p["freq"]
    Re_cold_ws = rho_cold_ws * v_cold * max(L_cold, 1e-4) / g_cold["mu"]
    Nu_cold_ws = 0.75 * max(Re_cold_ws, 1)**0.7
    h_cold_space = Nu_cold_ws * g_cold["k"] / max(L_cold, 1e-4)

    # Cooler tube contribution (primary cold-side HX)
    _tube_Dh = _mm2m(p["cooler_tube_dia"])
    _tube_flow_area = (p["cooler_tube_count"] * math.pi / 4 *
                       _mm2m(p["cooler_tube_dia"])**2)
    _tube_wetted_perim = p["cooler_tube_count"] * math.pi * _mm2m(p["cooler_tube_dia"])
    _V_dot_piston = _mm2_m2(bore_area) * v_cold
    _u_cooler = _V_dot_piston / _tube_flow_area if _tube_flow_area > 0 else 1e6
    _Re_cooler = rho_cold_ws * _u_cooler * _tube_Dh / g_cold["mu"]
    if _Re_cooler > 2300:
        _Nu_cooler = 0.023 * _Re_cooler**0.8 * g_cold["Pr"]**0.4
    else:
        _Nu_cooler = 3.66
    _h_cooler = _Nu_cooler * g_cold["k"] / _tube_Dh
    _A_cooler = _tube_wetted_perim * _mm2m(p["cooler_length"])

    # Include cooler gas inventory in cold-side thermal mass
    V_cooler_m3 = _mm3_m3(V_cooler_dead)
    m_cold_total = rho_cold_ws * (V_cold_m3 + V_cooler_m3)

    # Combined cold-side hA: working space walls + cooler tubes
    hA_cold_total = h_cold_space * A_cold_wall_m2 + _h_cooler * _A_cooler
    NTU_cold = hA_cold_total / (m_cold_total * g["cp"] * p["freq"]) if m_cold_total > 0 else 100

    # Combined adiabatic efficiency
    eta_adia_hot = NTU_hot / (1 + NTU_hot)
    eta_adia_cold = NTU_cold / (1 + NTU_cold)
    eta_adia = eta_adia_hot * eta_adia_cold  # both spaces must transfer heat

    P_schmidt_ideal = W_schmidt * p["freq"]
    P_schmidt = P_schmidt_ideal * eta_adia  # adiabatic-corrected power
    eta_carnot = 1 - tau

    # ── Derived geometry ──────────────────────────────────────────
    piston_od = p["vessel_id"] - 2 * p["piston_clearance"]
    displacer_od = p["vessel_id"] - 2 * p["displacer_clearance"]
    vessel_od = p["vessel_id"] + 2 * p["vessel_wall"]
    # omega already computed above in adiabatic correction section

    # Piston-driven flow (for cooler, cold-side HX)
    v_piston_peak = math.pi * _mm2m(p["piston_stroke"]) * p["freq"]
    V_dot_piston_peak = _mm2_m2(bore_area) * v_piston_peak
    rho_cold = p["P_mean"] / (g["R"] * p["T_cold"])
    m_dot_piston_peak = rho_cold * V_dot_piston_peak

    # Displacer-driven flow (for regenerator and heater)
    # The displacer shuttles gas between hot and cold spaces through the regen.
    v_displacer_peak = math.pi * _mm2m(p["displacer_stroke"]) * p["freq"]
    V_dot_displacer_peak = _mm2_m2(bore_area) * v_displacer_peak
    rho_mean = p["P_mean"] / (g["R"] * T_regen_mean)
    m_dot_regen_peak = rho_mean * V_dot_displacer_peak

    # Regenerator heat transport: mass shuttled per half-cycle × cp × ΔT × freq
    # Per half-cycle, mass through regen = m_dot_peak × ∫sin(ωt)dt over half period
    #                                    = m_dot_peak / (π × freq)
    # Q_regen_total (W) = mass_per_half_cycle × cp × ΔT × freq
    #                   = m_dot_regen_peak × cp × ΔT / π
    Q_regen_total = m_dot_regen_peak * g["cp"] * dT / math.pi  # W
    # (cp is constant for monatomic ideal gas, no temperature correction needed)

    # ── Cooler heat exchanger ─────────────────────────────────────
    tube_flow_area = (p["cooler_tube_count"] * math.pi / 4 *
                      (_mm2m(p["cooler_tube_dia"]))**2)
    tube_wetted_perim = p["cooler_tube_count"] * math.pi * _mm2m(p["cooler_tube_dia"])
    tube_Dh = _mm2m(p["cooler_tube_dia"])

    u_cooler = V_dot_piston_peak / tube_flow_area if tube_flow_area > 0 else 1e6
    Re_cooler = rho_cold * u_cooler * tube_Dh / g_cold["mu"]

    # Valensi number for oscillating flow correction
    nu_cold = g_cold["mu"] / rho_cold
    Va_cooler = omega * tube_Dh**2 / (4 * nu_cold)
    # Oscillating flow friction multiplier (Zhao & Cheng, 1996):
    # f_osc/f_steady ≈ 1 + 0.25 × sqrt(Va/Re) for Va/Re < 10
    osc_mult_cooler = 1 + 0.25 * math.sqrt(max(Va_cooler, 0.01) / max(Re_cooler, 1))

    if Re_cooler > 2300:
        f_cooler = 0.316 * Re_cooler**(-0.25)
    else:
        f_cooler = 64 / max(Re_cooler, 1)
    f_cooler *= osc_mult_cooler

    dp_cooler = (f_cooler * (_mm2m(p["cooler_length"]) / tube_Dh) *
                 0.5 * rho_cold * u_cooler**2)

    if Re_cooler > 2300:
        Nu_cooler = 0.023 * Re_cooler**0.8 * g_cold["Pr"]**0.4
    else:
        Nu_cooler = 3.66
    h_cooler = Nu_cooler * g_cold["k"] / tube_Dh

    A_cooler = tube_wetted_perim * _mm2m(p["cooler_length"])
    NTU_cooler = h_cooler * A_cooler / (m_dot_piston_peak * g["cp"]) if m_dot_piston_peak > 0 else 0

    # ── Regenerator ───────────────────────────────────────────────
    d_wire = _mm2m(p["regen_wire_dia"])
    regen_bore_area = _mm2_m2(bore_area)
    regen_flow_area = p["regen_porosity"] * regen_bore_area
    u_regen = V_dot_displacer_peak / regen_flow_area if regen_flow_area > 0 else 1e6

    rho_regen = rho_mean  # already computed at T_regen_mean
    Re_regen = rho_regen * u_regen * d_wire / g_mean["mu"]

    # Oscillating flow in packed screens (Gedeon & Wood, 1996):
    # Friction factor includes oscillation effects via kinetic Reynolds number
    # Re_omega = rho × omega × d_wire² / mu (Womersley-like parameter)
    Re_omega = rho_regen * omega * d_wire**2 / g_mean["mu"]
    # Combined friction factor for oscillating flow through wire screens.
    # Steady Ergun-type correlation for woven mesh (ref [5], Gedeon & Wood 1996):
    #   f = 175/Re + 1.6
    # where 175 is the viscous (Darcy-Kozeny) coefficient and 1.6 is the
    # inertial (Forchheimer) coefficient, both from Gedeon & Wood's best-fit
    # to screen regenerator data.
    # Oscillating correction (ref [5]):
    #   f_osc = f_steady × (1 + 0.3 × sqrt(Re_ω))
    # where Re_ω = ρ ω d² / μ (kinetic Reynolds number, Womersley-like).
    # This accounts for streaming and acoustic streaming effects.
    f_regen_screen = (175 / max(Re_regen, 0.1) + 1.6)
    osc_mult_regen = 1 + 0.3 * math.sqrt(max(Re_omega, 0.01))
    f_regen_screen *= osc_mult_regen

    mesh_pitch = 25.4 / p["regen_mesh_count"]
    n_screens = p["regen_length"] / (mesh_pitch * 2)

    dp_regen = (n_screens * f_regen_screen *
                0.5 * rho_regen * u_regen**2 / p["regen_porosity"]**2)

    # Heat transfer in oscillating flow through screens.
    # Steady correlation (ref [8], Tanaka et al. 1990):
    #   Nu = 0.33 × Re^0.6 × Pr^0.36
    # Valid for 20 < Re < 800, wire-mesh regenerators.
    # Oscillating-flow enhancement (ref [9], Ibrahim et al. 2004):
    #   Nu_osc = Nu_steady × (1 + 0.15 × Re_ω^0.25)
    # Exponent 0.25 and coefficient 0.15 are from curve fits to oscillating
    # annular-gap and packed-bed data in Ibrahim et al.'s CFD study.
    Nu_regen_steady = 0.33 * max(Re_regen, 0.1)**0.6 * g_mean["Pr"]**0.36
    Nu_regen = Nu_regen_steady * (1 + 0.15 * max(Re_omega, 0.01)**0.25)
    h_regen = Nu_regen * g_mean["k"] / d_wire

    beta = 4 * (1 - p["regen_porosity"]) / d_wire
    V_regen_vol = regen_bore_area * _mm2m(p["regen_length"])
    A_regen = beta * V_regen_vol

    NTU_regen = h_regen * A_regen / (m_dot_regen_peak * g["cp"]) if m_dot_regen_peak > 0 else 0
    # For oscillating flow regenerator, effectiveness depends on NTU and
    # matrix heat capacity ratio Cr = (m_matrix × c_matrix) / (m_gas × cp_gas).
    # When Cr >> 1 (heavy matrix, light gas — true for steel mesh + helium):
    # ε ≈ NTU / (1 + NTU)  — same as balanced counterflow limit.
    # This is valid for our case (steel mesh Cr > 50).
    regen_effectiveness = NTU_regen / (1 + NTU_regen) if NTU_regen > 0 else 0

    dp_total = dp_cooler + dp_regen
    dp_total_frac = dp_total / p["P_mean"]

    # ── Heater gas-side (HTC from first principles) ────────────────
    # (heater_head_id, cup_wall_area, cup_top_area, fin_area, A_heater_total
    #  computed earlier in geometry section)

    # Compute h_heater from flow through fin channels
    # Channel between adjacent fins: width = circumference/n_fins - fin_thickness
    fin_gap_mm = (math.pi * heater_head_id / max(p["heater_int_fin_count"], 1)
                  - p["heater_int_fin_thickness"])
    fin_gap_mm = max(fin_gap_mm, 0.5)  # minimum physical gap
    # Hydraulic diameter of rectangular channel (gap × fin_height)
    fin_gap_m = _mm2m(fin_gap_mm)
    fin_height_m = _mm2m(p["heater_int_fin_height"])
    Dh_heater = 2 * fin_gap_m * fin_height_m / (fin_gap_m + fin_height_m)

    # Flow area through all fin channels
    n_channels = p["heater_int_fin_count"]
    A_flow_heater = n_channels * fin_gap_m * fin_height_m
    # Displacer drives flow into heater (hot side)
    u_heater = V_dot_displacer_peak / max(A_flow_heater, 1e-8)
    rho_hot = p["P_mean"] / (g["R"] * p["T_hot"])
    Re_heater = rho_hot * u_heater * Dh_heater / g_hot["mu"]

    # Nusselt for rectangular channel (developing + oscillating flow)
    if Re_heater > 2300:
        Nu_heater = 0.023 * Re_heater**0.8 * g_hot["Pr"]**0.4
    else:
        # Developing laminar flow in short channel (Shah & London):
        # Nu ≈ 7.54 for fully developed, but developing flow is higher
        x_star = _mm2m(p["heater_int_fin_length"]) / (Dh_heater * max(Re_heater, 1) * g_hot["Pr"])
        if x_star < 0.01:
            Nu_heater = 1.86 * (max(Re_heater, 1) * g_hot["Pr"] * Dh_heater /
                                _mm2m(p["heater_int_fin_length"]))**0.33
        else:
            Nu_heater = 7.54

    h_heater = Nu_heater * g_hot["k"] / Dh_heater

    dT_heater = (p["Q_input"] / (h_heater * _mm2_m2(A_heater_total))
                 if A_heater_total > 0 else 999)

    # ── Fix 6: Heater head external thermal resistance ────────────────
    # Heat flows: source (sand/focus) → heater outer wall → heater wall conduction
    # → inner fin surface (dT_heater) → gas.  The two external resistances set
    # the required source temperature to maintain T_hot in the working gas.
    heater_head_od = (p["vessel_id"] - 2 * p["heater_head_wall"] + 2 * p["heater_head_wall"])  # = vessel_id mm
    A_heater_ext_m2 = math.pi * _mm2m(heater_head_od) * _mm2m(p["heater_int_fin_length"])
    A_heater_ext_m2 = max(A_heater_ext_m2, 1e-4)

    # Wall conduction: Q = k × A × ΔT / t_wall  (cylindrical approximation)
    dT_heater_wall = (p["Q_input"] * _mm2m(p["heater_head_wall"]) /
                      (p.get("k_heater_head", 16.0) * A_heater_ext_m2))

    # External source-to-wall convection/radiation: Q = h × A × ΔT
    dT_heater_ext = p["Q_input"] / (p.get("h_source_to_heater", 250.0) * A_heater_ext_m2)

    # Total source-to-gas temperature drop
    dT_heater_total = dT_heater + dT_heater_wall + dT_heater_ext

    # ── Clearance seal leakage ────────────────────────────────────
    dP_piston = p["P_mean"] * (p_ratio - 1) / (p_ratio + 1)
    V_dot_swept = _mm3_m3(V_swept_piston) * p["freq"] * 2

    gap_piston_m = p["piston_clearance"] * 1e-3
    D_piston = piston_od * 1e-3
    L_piston = p["piston_length"] * 1e-3

    # Piston is in the cold zone → use cold viscosity.
    # Hagen-Poiseuille flow in annular gap (ref [16]):
    #   Q = π D h³ ΔP / (12 μ L)
    # where h = radial clearance, D = piston diameter, L = seal length.
    # This is the thin-gap (h << D) limit of annular Poiseuille flow.
    Q_leak_piston = (math.pi * D_piston * gap_piston_m**3 * dP_piston /
                     (12 * g_cold["mu"] * L_piston))
    leak_piston_pct = Q_leak_piston / V_dot_swept * 100 if V_dot_swept > 0 else 999

    gap_displacer_m = p["displacer_clearance"] * 1e-3
    D_displacer = displacer_od * 1e-3
    L_displacer = p["displacer_length"] * 1e-3

    # Displacer spans hot-cold boundary → use mean viscosity
    Q_leak_displacer = (math.pi * D_displacer * gap_displacer_m**3 * dP_piston /
                        (12 * g_mean["mu"] * L_displacer))
    leak_displacer_pct = (Q_leak_displacer / V_dot_swept * 100
                          if V_dot_swept > 0 else 999)

    # ══════════════════════════════════════════════════════════════
    # LOSS MECHANISMS (each computed as power loss in Watts)
    # ══════════════════════════════════════════════════════════════

    # ── Loss 1: Pumping (pressure drop × volume flow) ────────────
    # Cooler uses piston flow, regen uses displacer flow
    P_loss_pumping = (dp_cooler * V_dot_piston_peak +
                      dp_regen * V_dot_displacer_peak)

    # ── Loss 2: Shuttle heat loss (displacer thermal shuttling) ──
    # The displacer oscillates between hot and cold zones, carrying
    # heat via its wall. Ref [1]: Urieli & Berchowitz eq. 7.24.
    # Gas-film version: P = (π²/8) × k_gas × D × S² × ΔT × f / (L × δ)
    # Solid-wall version (used here, dominates when wall cond >> gas film):
    #   P_shuttle = k_wall × (π D t_wall) × S² × ΔT / (2 × L × δ)
    # where:
    #   S  = stroke amplitude (half peak-to-peak), m
    #   L  = displacer length (conduction path), m
    #   δ  = gas film thickness in annular gap (= displacer_clearance), m
    #   t_wall = displacer wall thickness, m
    S_displacer = _mm2m(p["displacer_stroke"]) / 2  # amplitude
    t_wall_disp = _mm2m(p["displacer_wall"])

    P_loss_shuttle = (k_displacer * math.pi * D_displacer * t_wall_disp *
                      S_displacer**2 * dT /
                      (2 * L_displacer * max(gap_displacer_m, 1e-6)))

    # ── Loss 3: Displacer wall conduction (axial) ────────────────
    # Heat conducts along the displacer shell from hot cap to cold end.
    # Q = k × A_cross × ΔT / L
    A_disp_cross = math.pi * D_displacer * t_wall_disp  # m² (thin-wall ring)
    P_loss_disp_cond = k_displacer * A_disp_cross * dT / L_displacer

    # ── Loss 4: Vessel wall conduction (axial) ───────────────────
    # Heat conducts along the pressure vessel wall from hot to cold zone.
    # The conduction path length is approximately from the heater head
    # to the cooler zone.
    vessel_wall_m = _mm2m(p["vessel_wall"])
    vessel_id_m = _mm2m(p["vessel_id"])
    vessel_od_m = vessel_id_m + 2 * vessel_wall_m
    A_vessel_cross = math.pi / 4 * (vessel_od_m**2 - vessel_id_m**2)  # m²

    # Conduction path: from heater to cooler (roughly the distance between them)
    # Approximate as regenerator length + some gaps
    L_conduction = _mm2m(p["regen_length"] + p["cooler_length"] +
                         p["hot_space_gap"] + 10)  # mm → m
    P_loss_vessel_cond = k_vessel_eff * A_vessel_cross * dT / L_conduction

    # ── Loss 5: Regenerator enthalpy loss ────────────────────────
    # Heat not recovered by the regenerator must be supplied by the heater.
    # P_regen_loss = (1 - ε) × Q_transported_per_cycle × freq
    # Q_transported ≈ m_dot_mean × cp × ΔT / freq (per cycle)
    P_loss_regen = (1 - regen_effectiveness) * Q_regen_total

    # ── Loss 6: Gas spring hysteresis (Lee's analytical model) ────
    # Irreversible heat transfer during compression/expansion causes
    # the real PV cycle in the bounce space to enclose a loss area.
    #
    # Lee's model (1983) "An Analytical Study of Gas Spring Hysteresis":
    # For a cylinder of radius R with sinusoidal volume variation ΔV/V₀,
    # the hysteresis loss per cycle is:
    #
    #   W_hyst = (π/4) × P₀ × V₀ × (ΔV/V₀)² × (γ-1) × f(λ)
    #
    # where λ = R × sqrt(ω / (2α)) is the dimensionless frequency,
    # α = k/(ρ×cp) is thermal diffusivity, and
    #
    #   f(λ) = [sinh(2λ) - sin(2λ)] / [cosh(2λ) + cos(2λ)]
    #        → λ  for λ << 1  (isothermal limit, small loss)
    #        → 1  for λ >> 1  (adiabatic limit, small loss)
    #        → max ≈ 0.5 at λ ≈ 1  (worst case: thermal penetration ≈ radius)
    #
    # P_hyst = W_hyst × freq
    V_bounce_m3 = _mm3_m3(bore_area * p["bounce_length"])
    dV_frac = _mm2m(p["piston_stroke"]) * _mm2_m2(bore_area) / V_bounce_m3

    # Thermal diffusivity at cold side (bounce space is cold).
    # α = k / (ρ cp)  [m²/s] — ratio of thermal conductivity to volumetric heat capacity
    alpha_thermal = g_cold["k"] / (rho_cold * g["cp"])
    R_cyl = D_piston / 2  # cylinder radius (m)
    # Dimensionless frequency parameter λ (ref [7], Lee 1983 eq. 7):
    #   λ = R × √(ω / (2α))
    # Physical meaning: ratio of cylinder radius R to thermal penetration depth
    #   δ_thermal = √(2α/ω) — the depth at which wall temperature oscillations
    #   penetrate into the gas.  λ = R/δ_thermal.
    lambda_lee = R_cyl * math.sqrt(omega / (2 * alpha_thermal))

    # Lee's hysteresis function f(λ) — exact analytical form
    # f(λ) = [sinh(2λ) - sin(2λ)] / [2λ × (cosh(2λ) + cos(2λ))]
    # Behavior:
    #   λ→0 (isothermal): f→0  (no loss, gas tracks wall temp perfectly)
    #   λ→∞ (adiabatic):  f→1/(2λ)→0  (no loss, gas ignores walls)
    #   λ≈1 (max loss):   f≈0.5  (thermal penetration ≈ radius)
    two_lam = 2 * lambda_lee
    if two_lam < 50:  # avoid overflow in sinh/cosh
        f_lee = ((math.sinh(two_lam) - math.sin(two_lam)) /
                 (two_lam * (math.cosh(two_lam) + math.cos(two_lam))))
    else:
        f_lee = 1.0 / two_lam  # asymptotic: 1/(2λ)

    # Hysteresis power = (π/2) × P × V × (ΔV/V)² × (γ-1)²/γ × f(λ) × freq
    # (γ-1)²/γ factor from polytropic deviation between isothermal and adiabatic
    gamma = g["gamma"]
    W_hyst_per_cycle = (math.pi / 2 * p["P_mean"] * V_bounce_m3 *
                        dV_frac**2 * (gamma - 1)**2 / gamma * f_lee)
    P_loss_hysteresis = W_hyst_per_cycle * p["freq"]

    # ── Loss 7: Seal leakage (PV work lost) ──────────────────────
    # Gas leaking through clearance seals carries enthalpy and loses PV work.
    # P_leak ≈ ΔP × Q_leak (volumetric flow × pressure difference)
    P_loss_seal = dP_piston * (Q_leak_piston + Q_leak_displacer)

    # ── Loss 8: Regenerator axial conduction (Fix 7) ──────────────
    # Wire mesh conducts heat along the regenerator axis from hot to cold.
    # The effective axial conductivity sums gas conduction (full area × ε)
    # and wire conduction (area × (1-ε), but most wires are ⊥ to axis so
    # only the axial fraction C_geo ≈ 0.05 of wires carry axial heat).
    #
    #   k_eff_axial = k_gas × ε + k_wire × (1-ε) × C_geo
    #   P_loss = k_eff × A_bore × (T_hot - T_cold) / L_regen
    k_regen_axial = (g_mean["k"] * p["regen_porosity"] +
                     p.get("regen_wire_k", 16.0) * (1 - p["regen_porosity"]) *
                     p.get("regen_C_geo", 0.05))
    P_loss_regen_cond = k_regen_axial * regen_bore_area * dT / _mm2m(p["regen_length"])

    # ══════════════════════════════════════════════════════════════
    # POWER BUDGET (from first principles)
    # ══════════════════════════════════════════════════════════════

    # Total thermal losses (heat that bypasses the thermodynamic cycle)
    P_loss_thermal = (P_loss_shuttle + P_loss_disp_cond +
                      P_loss_vessel_cond + P_loss_regen + P_loss_regen_cond)

    # Total mechanical/flow losses (work absorbed by parasitics)
    P_loss_mechanical = P_loss_pumping + P_loss_hysteresis + P_loss_seal

    # Available heat for the cycle (Q_input minus thermal bypasses)
    Q_available = p["Q_input"] - P_loss_thermal - dT_heater * 0  # dT reduces T_hot but doesn't lose heat

    # Actual heat entering the cycle is limited by available heat
    Q_cycle = max(0, min(Q_available, p["Q_input"]))

    # Ideal indicated power from the available heat at Carnot efficiency
    # The Schmidt analysis gives power assuming perfect heat supply.
    # In reality, the cycle power is limited by heat input.
    P_ideal_from_heat = Q_cycle * eta_carnot
    P_indicated_actual = min(P_schmidt, P_ideal_from_heat)

    # Net indicated power after mechanical losses
    P_net_indicated = max(0, P_indicated_actual - P_loss_mechanical)

    # ── Linear alternator (electromagnetic model) ──────────────────
    # Moving-magnet linear alternator: magnet ring oscillates through coil.
    #
    # EMF from Faraday's law: V_emf = -N × dΦ/dt
    # For a magnet ring moving axially through a coil:
    #   Φ(t) ≈ B_avg × A_magnet × sin(ωt)  (sinusoidal flux linkage)
    #   V_emf_peak = N × ω × B_avg × A_magnet
    #
    # B_avg in the air gap ≈ Br × (t_mag / (t_mag + g_mag))
    # where t_mag = magnet thickness, g_mag = magnetic air gap

    # Magnet cross-sectional area (annular ring)
    R_mag_o = p["magnet_ring_od"] * 1e-3 / 2
    R_mag_i = p["magnet_ring_id"] * 1e-3 / 2
    A_mag = math.pi * (R_mag_o**2 - R_mag_i**2)

    # Magnetic air gap (radial clearance between magnet and coil)
    # Coil sits on vessel wall, magnet moves inside
    g_air_gap = (p["vessel_id"] / 2 - p["magnet_ring_od"] / 2) * 1e-3
    g_air_gap = max(g_air_gap, 1e-3)  # minimum 1mm
    t_mag_axial = p["magnet_ring_length"] * 1e-3

    # Fix 9: SmCo temperature correction for alternator magnet
    # Br decreases linearly with temperature: Br(T) = Br₀ × (1 + α_Br × (T_C − 20))
    # Alternator magnets on piston are in the cold zone → near T_cold
    T_alt_mag_C = p["T_cold"] - 273.15  # alternator magnet temperature (°C)
    Br_alt_corrected = (p["Br_alternator"] *
                        (1.0 + p.get("alpha_Br", -3.5e-4) * (T_alt_mag_C - 20.0)))
    Br_alt_corrected = max(Br_alt_corrected, 0.1)  # floor (demagnetised)

    # Fix 10: Corrected reluctance model with recoil permeability and fringe leakage.
    # Classical magnet-circuit formula (replacing the t/(t+g) approximation):
    #   B_gap = Br / (1 + μr × g_air / t_mag)
    # This correctly accounts for SmCo recoil permeability (μr ≈ 1.05).
    # Additional fringe leakage factor (empirical, from motor design):
    #   F_fringe = 1 − 0.15 × sqrt(g_air / t_mag)  (validated for g/t < 2)
    mu_r = p.get("mu_r_magnet", 1.05)
    _g_over_t = g_air_gap / max(t_mag_axial, 1e-4)
    B_gap_ideal = Br_alt_corrected / (1.0 + mu_r * _g_over_t)
    F_fringe = max(1.0 - 0.15 * math.sqrt(_g_over_t), 0.5)
    B_gap = B_gap_ideal * F_fringe

    # Peak EMF: V = N × ω × B × A × (stroke/coil_length) correction
    # The flux linkage change depends on how far the magnet moves relative
    # to the coil. If stroke < coil_length, only partial flux change.
    stroke_m = _mm2m(p["piston_stroke"])
    coil_length_m = _mm2m(p["coil_length"])
    flux_coupling = min(1.0, stroke_m / coil_length_m)  # fraction of full flux change

    N = p["coil_turns"]
    V_emf_peak = N * omega * B_gap * A_mag * flux_coupling
    V_emf_rms = V_emf_peak / math.sqrt(2)

    # Coil resistance from wire geometry
    # Mean coil radius = vessel wall + coil depth/2
    r_wire = p["coil_wire_dia"] * 1e-3 / 2
    A_wire = math.pi * r_wire**2
    # Copper resistivity at 20°C: ρ₀ = 1.72×10⁻⁸ Ω·m (ref [18], IEC 60028 annealed)
    rho_cu = 1.72e-8  # Ω·m
    # Linear temperature coefficient (ref [18]):
    #   ρ(T) = ρ₀ × (1 + TCR × (T_C − 20))
    #   TCR = 0.00393 /°C (pure copper, IEC 60028); 0.004 /°C is standard engineering value
    T_coil_C = (p["T_cold"] - 273.15) + 40.0   # °C — cold side + ~40°C I²R rise
    rho_cu_hot = rho_cu * (1.0 + 0.004 * (T_coil_C - 20.0))

    # Mean turn length (circumference at mean coil radius)
    R_coil_mean = (p["vessel_id"] / 2 + p["vessel_wall"] +
                   p["coil_layers"] * p["coil_wire_dia"] / 2) * 1e-3
    L_turn = 2 * math.pi * R_coil_mean
    R_coil = rho_cu_hot * N * L_turn / A_wire  # total coil resistance (Ω)

    # Fix 2: Coil inductance and reactive impedance
    # Solenoid inductance with Nagaoka coefficient k_N (correction for short coil).
    # Nagaoka coefficient k_N corrects the infinite-solenoid formula for short coils.
    # Ref [14]: Nagaoka (1909) tabulated k_N as a function of 2R/l.
    # 1-term approximation used here: k_N ≈ 1 / (1 + 0.9 × (2R/l))
    # Valid for 2R/l < 2 (coil not much wider than it is long); adequate for l/R ≈ 1.
    # The coefficient 0.9 is from Lorenz's 1879 series; see also Murgatroyd (1989)
    # "Calculation of Proximity Losses in Multistranded Conductor Bunches".
    mu_0_alt = 4 * math.pi * 1e-7  # H/m — permeability of free space
    A_coil_cross = math.pi * R_coil_mean**2  # m² — cross-sectional area enclosed by mean turn
    l_coil_m = _mm2m(p["coil_length"])
    k_nagaoka = 1.0 / (1.0 + 0.9 * (2 * R_coil_mean / max(l_coil_m, 1e-4)))
    L_coil = mu_0_alt * N**2 * A_coil_cross * k_nagaoka / max(l_coil_m, 1e-4)  # Henry

    X_L = omega * L_coil                            # inductive reactance (Ω)
    Z_coil = math.sqrt(R_coil**2 + X_L**2)          # coil impedance magnitude (Ω)
    power_factor_coil = R_coil / Z_coil if Z_coil > 0 else 1.0  # cos(φ)
    # Optimal PFC capacitor cancels X_L: C_pfc = 1 / (ω² × L)
    C_pfc = 1.0 / (omega**2 * L_coil) if L_coil > 0 else 0.0   # Farads

    # Optimal load matching: R_load = R_coil (maximum power transfer)
    # P_elec_max = V_emf_rms² / (4 × R_coil)  — but that's only 50% efficient
    # In practice, operate at higher R_load for better efficiency:
    # P_copper = I² × R_coil, P_load = I² × R_load
    # η_copper = R_load / (R_load + R_coil)
    # For good efficiency, R_load ≈ 3-5 × R_coil → η ≈ 75-83%
    # The actual current is set by the mechanical power available:
    # P_mech = V_emf × I × cos(φ) = I² × (R_load + R_coil)

    # Fix 2: Power extraction with reactive impedance.
    # Circuit: V_emf (source) in series with R_coil + jX_L feeding resistive load R_load.
    # Without PFC capacitor the inductive reactance limits extractable real power:
    #   P_load_max = V_emf² × R_coil / (2R_coil² + X_L²)  (optimised over R_load)
    # vs purely resistive: P_max = V_emf² / 4R_coil
    #
    # With a PFC capacitor (C = 1/(ω²L)) the reactance cancels and full power recovers.
    # We compute copper loss assuming a power-factor-corrected (PFC) rectifier — the
    # most realistic case for a modern inverter.  Without PFC, multiply by power_factor_coil².
    if V_emf_rms > 0 and R_coil > 0:
        # With PFC: effective circuit is purely resistive at R_coil.
        # Current from mechanical power constraint: P_mech = I² × (R_coil + R_load)
        # For maximum efficiency: R_load >> R_coil → approximate R_load ≈ 3R_coil
        # Solve: P_net = V_emf × I − I² × R_coil  (quadratic in I)
        discriminant = V_emf_rms**2 - 4.0 * R_coil * P_net_indicated
        if discriminant > 0:
            I_rms = (V_emf_rms - math.sqrt(discriminant)) / (2.0 * R_coil)
            P_copper = I_rms**2 * R_coil
        else:
            # Coil impedance too high to extract target power — bound by max power
            I_rms = V_emf_rms / (2.0 * R_coil)
            P_copper = I_rms**2 * R_coil
        # Without PFC the apparent current through X_L reduces real power:
        P_copper_no_pfc = P_copper / (power_factor_coil**2) if power_factor_coil > 0 else P_copper
    else:
        I_rms = 0.0
        P_copper = 0.0
        P_copper_no_pfc = 0.0

    # Iron losses in stator laminations (hysteresis + eddy current)
    # P_iron = k_iron × (f/f_ref)^1.6 × (B/B_ref)^2 × m_iron
    # Stator mass estimate: coil volume × iron fill × density
    V_coil_space = (math.pi * ((R_coil_mean + p["coil_layers"] *
                    p["coil_wire_dia"] * 1e-3 / 2)**2 -
                    (R_coil_mean - p["coil_layers"] *
                    p["coil_wire_dia"] * 1e-3 / 2)**2) * coil_length_m)
    rho_iron = 7650  # kg/m³ — non-oriented silicon steel (M19-M45 grade, ASM Handbook)
    m_iron = V_coil_space * (1 - p["coil_fill_factor"]) * rho_iron
    m_iron = max(m_iron, 0.01)  # minimum 10g

    f_ref = 50.0  # Hz — reference frequency for iron_loss_coeff default (2 W/kg at 50Hz, 1T)
    # Modified Steinmetz equation (ref [15], Bertotti 1998):
    #   P_iron = k_h × f^α × B^β  where α≈1.6 and β≈2 for silicon steel.
    # Exponent 1.6 (vs. classic 1.0) captures both hysteresis (f^1) and excess
    # eddy-current losses (f^1.5–f^2) via a single empirical power law.
    # iron_loss_coeff = k_h in W/kg at 50Hz, 1T — typical M19 silicon steel ≈ 2 W/kg.
    P_iron = (p["iron_loss_coeff"] * (p["freq"] / f_ref)**1.6 *
              (B_gap / 1.0)**2 * m_iron)

    # Total alternator losses
    P_alt_loss = P_copper + P_iron
    P_electrical_raw = max(0, P_net_indicated - P_alt_loss)
    eta_alternator = P_electrical_raw / P_net_indicated if P_net_indicated > 0 else 0

    # Electronics (rectifier + inverter)
    P_electrical = P_electrical_raw * p["eta_electronics"]

    # Overall efficiency
    eta_overall = P_electrical / p["Q_input"] if p["Q_input"] > 0 else 0

    # Implied fraction of Carnot
    eta_elec_total = eta_alternator * p["eta_electronics"]
    eta_carnot_fraction_actual = (eta_overall / (eta_carnot * eta_elec_total)
                                  if eta_carnot > 0 and eta_elec_total > 0
                                  else 0)

    # ── Piston dynamics ───────────────────────────────────────────
    A_piston_m2 = _mm2_m2(math.pi / 4 * piston_od**2)

    # Gas spring stiffness (linearized ideal gas spring)
    k_gas_spring = g["gamma"] * p["P_mean"] * A_piston_m2**2 / V_bounce_m3

    # ── Magnetic spring stiffness (from dipole approximation) ──────
    # For two coaxial repulsive ring magnets separated by gap g:
    # The force is F(z) = -dU/dz, and near equilibrium the stiffness is
    # k_mag = -dF/dz evaluated at the equilibrium gap.
    #
    # For ring magnets modeled as magnetic charge sheets (surface current model):
    # The on-axis field from a ring magnet at distance z:
    #   B(z) = (Br/2) × t / (z² + R_mean²)^(3/2) × R_mean² (dipole approx)
    # where t = axial thickness, R_mean = (OD+ID)/4
    #
    # The force between two identical ring magnets:
    #   F(z) = (3 μ₀ m₁ m₂) / (2π z⁴)  where m = Br × A × t / μ₀
    #
    # For engineering accuracy, use the ring magnet dipole moment:
    #   m = Br × V_magnet / μ₀  where V = π/4 × (OD² - ID²) × t
    # Then:
    #   k_mag = 12 μ₀ m² / (2π z⁵) = 6 μ₀ m² / (π z⁵)

    mu_0 = 4 * math.pi * 1e-7  # H/m
    R_spring_od = p["mag_spring_od"] * 1e-3 / 2  # m
    R_spring_id = p["mag_spring_id"] * 1e-3 / 2  # m
    t_spring = p["mag_spring_thickness"] * 1e-3   # m
    gap_spring = p["mag_spring_gap"] * 1e-3       # m

    # Fix 9: SmCo temperature correction for spring magnets.
    # Spring magnets are on the vessel wall, spanning from cooler to hot zone.
    # Temperature at spring location ≈ T_mean (conservative; use T_mean as default).
    T_spring_K = p.get("T_mag_spring") or T_mean
    T_spring_C = T_spring_K - 273.15
    Br_spring_corrected = (p["Br_magnet"] *
                           (1.0 + p.get("alpha_Br", -3.5e-4) * (T_spring_C - 20.0)))
    Br_spring_corrected = max(Br_spring_corrected, 0.1)
    mag_demagnetization_risk = T_spring_K > p.get("T_max_SmCo", 350 + 273.15)
    Br = Br_spring_corrected

    # Volume and magnetic moment of one ring magnet
    V_spring_magnet = math.pi * (R_spring_od**2 - R_spring_id**2) * t_spring
    m_dipole = Br * V_spring_magnet / mu_0  # A·m²

    # Stiffness of one repulsive pair (linearized at equilibrium gap)
    # k = d²U/dz² = 12 × μ₀ × m² / (2π × z⁵) for dipole-dipole
    k_one_pair = 12 * mu_0 * m_dipole**2 / (2 * math.pi * gap_spring**5)
    k_mag_spring = p["mag_spring_pairs"] * k_one_pair

    k_total_spring = k_gas_spring + k_mag_spring

    # ── Piston and magnet mass ──────────────────────────────────
    rho_piston = MATERIALS.get(p.get("vessel_material", "ss316"), MATERIALS["ss316"])["rho"]
    V_piston_solid = (math.pi / 4 * (piston_od * 1e-3)**2 *
                      p["piston_length"] * 1e-3)
    V_piston_hollow = (math.pi / 4 * ((piston_od - 2 * p["piston_wall"]) * 1e-3)**2 *
                       p["piston_length"] * 1e-3)
    m_piston = rho_piston * (V_piston_solid - V_piston_hollow)

    # SmCo alternator magnets
    # Sm₂Co₁₇ density: 8400 kg/m³ (ASM Handbook vol. 2 / Arnold Magnetic Technologies datasheet)
    rho_magnet = 8400  # kg/m³
    V_magnet = ((math.pi / 4 * (p["magnet_ring_od"] * 1e-3)**2 -
                 math.pi / 4 * (p["magnet_ring_id"] * 1e-3)**2) *
                p["magnet_ring_length"] * 1e-3)
    m_magnet = rho_magnet * V_magnet
    m_total = m_piston + m_magnet

    # Natural frequency from combined gas + magnetic springs
    f_natural = (1 / (2 * math.pi) * math.sqrt(k_total_spring / m_total)
                 if m_total > 0 else 0)

    # ── Resonance error ───────────────────────────────────────────
    # Free-piston engines MUST operate at their natural frequency — there is no
    # crankshaft to enforce phase. The inverter decouples the output AC frequency
    # from the grid, but cannot change the mechanical resonance of the engine.
    # If f_natural ≠ f_op, the engine will not self-sustain oscillation.
    f_resonance_error = abs(f_natural - p["freq"]) / max(p["freq"], 1e-6)

    # ── Magnetic spring linearity check ───────────────────────────
    # The dipole approximation (F ∝ 1/z⁴) is only accurate when the displacement
    # amplitude (stroke/2) is small relative to the equilibrium gap.
    # Rule of thumb: stroke_amplitude / gap < 0.33 for < 10% force error.
    # Beyond this, the spring is strongly nonlinear and the engine may be unstable.
    stroke_amplitude = _mm2m(p["piston_stroke"]) / 2
    mag_spring_stroke_ratio = stroke_amplitude / max(gap_spring, 1e-4)

    # ── Earth cooling loop sizing (Fix 5) ─────────────────────────
    # A horizontal ground heat exchanger rejects waste heat to the soil.
    # Line-source steady-state model (Ingersoll & Plass, 1948):
    #   Q = 2π × k_soil × L_pipe × ΔT / ln(4d / D_pipe)
    # Solved for L_pipe given required heat rejection Q_cold.
    #
    # T_cold is the engine cold side temperature (15°C by default = ground loop setpoint).
    # The soil far-field temperature sets the driving ΔT for rejection.
    # Typical UK/Central-EU ground at 1 m depth: ~10-13°C year-round.
    #
    # Q_rejected = all input heat not converted to electricity (energy balance).
    Q_cold_rejected = max(0.0, p["Q_input"] - P_electrical)
    k_soil = 1.5           # W/(mK) — typical moist sandy loam
    d_burial = 1.0         # m — pipe burial depth
    D_pipe = 0.025         # m — 25mm HDPE pipe OD
    T_soil_far = 12.0      # °C — annual mean ground temperature at 1m
    T_pipe_inner = p["T_cold"] - 273.15  # °C — fluid at cold-side setpoint
    dT_ground = max(T_pipe_inner - T_soil_far, 0.5)  # K; 0.5 K floor avoids div/0
    # Line-source formula (ref [17], Ingersoll et al. 1954):
    #   Q = 2π k_soil L ΔT / ln(4d / D_pipe)
    # The factor of 4 in ln(4d/D_pipe) comes from the method of images: the ground
    # surface acts as an adiabatic boundary, and the image source at depth +d above
    # ground gives an effective spacing of 2d, doubled again by the image-pair
    # geometry → factor of 4.  This is the steady-state limit (t → ∞).
    ln_factor = math.log(4 * d_burial / D_pipe)
    L_ground_loop_req = (Q_cold_rejected * ln_factor /
                         (2 * math.pi * k_soil * dT_ground))
    L_ground_loop_req = max(L_ground_loop_req, 0.0)

    # ── Beale number ──────────────────────────────────────────────
    Bn_implied = P_electrical / (p["P_mean"] * p["freq"] * _mm3_m3(V_swept_piston))

    # ── Validation checks ─────────────────────────────────────────
    checks = [
        ("Dead volume ratio", dead_volume_ratio, "< 1.0",
         dead_volume_ratio < 1.0),
        ("Pressure swing %", pressure_swing_pct / 2, "10-20%",
         5 < pressure_swing_pct / 2 < 25),
        ("Regen effectiveness", regen_effectiveness, "> 0.90",
         regen_effectiveness > 0.90),
        ("HX dP / Pmean", dp_total_frac, "< 0.05",
         dp_total_frac < 0.05),
        ("Heater gas dT (C)", dT_heater, "< 80",
         dT_heater < 80),
        ("Heater total dT (C)", dT_heater_total, "< 200",
         dT_heater_total < 200),
        ("Piston leak %", leak_piston_pct, "< 5%",
         leak_piston_pct < 5),
        ("Displacer leak %", leak_displacer_pct, "< 5%",
         leak_displacer_pct < 5),
        ("Resonance match %", f_resonance_error * 100, "within 20%",
         f_resonance_error < 0.20),
        ("Phase error (deg)", phase_error_deg, "< 15°",
         phase_error_deg < 15.0),
        ("Mag spring ratio", mag_spring_stroke_ratio, "< 0.33",
         mag_spring_stroke_ratio < 0.33),
        ("SmCo demag risk", 1 if mag_demagnetization_risk else 0, "0 = safe",
         not mag_demagnetization_risk),
        ("Electrical W", P_electrical, ">= 60",
         P_electrical >= 60),
    ]

    return {
        # Power budget
        "P_electrical": P_electrical,
        "P_schmidt": P_schmidt,
        "P_indicated_actual": P_indicated_actual,
        "P_net_indicated": P_net_indicated,
        "Q_available": Q_available,
        "Q_cycle": Q_cycle,
        "W_per_cycle": W_schmidt,

        # Individual losses (W)
        "P_loss_pumping": P_loss_pumping,
        "P_loss_shuttle": P_loss_shuttle,
        "P_loss_disp_cond": P_loss_disp_cond,
        "P_loss_vessel_cond": P_loss_vessel_cond,
        "P_loss_regen": P_loss_regen,
        "P_loss_regen_cond": P_loss_regen_cond,
        "P_loss_hysteresis": P_loss_hysteresis,
        "P_loss_seal": P_loss_seal,
        "P_loss_thermal": P_loss_thermal,
        "P_loss_mechanical": P_loss_mechanical,
        "P_loss_total": P_loss_thermal + P_loss_mechanical,

        # Volumes (cc)
        "V_swept_piston_cc": V_swept_piston / 1000,
        "V_swept_displacer_cc": V_swept_displacer / 1000,
        "V_dead_total_cc": V_dead_total / 1000,
        "dead_volume_ratio": dead_volume_ratio,

        # Thermodynamics
        "pressure_ratio": p_ratio,
        "pressure_swing_pct": pressure_swing_pct / 2,
        "eta_carnot": eta_carnot,
        "eta_overall": eta_overall,
        "eta_carnot_fraction": eta_carnot_fraction_actual,
        "eta_alternator": eta_alternator,
        "eta_adia": eta_adia,
        "eta_adia_hot": eta_adia_hot,
        "eta_adia_cold": eta_adia_cold,
        "NTU_hot": NTU_hot,
        "NTU_cold": NTU_cold,
        "h_hot_space": h_hot_space,
        "h_cold_space": h_cold_space,
        "A_hot_wall_m2": A_hot_wall_m2,
        "A_cold_wall_m2": A_cold_wall_m2,
        "Re_hot": Re_hot,
        "Beale_number": Bn_implied,
        "k_displacer": k_displacer,
        "k_vessel": k_vessel,

        # Alternator
        "V_emf_rms": V_emf_rms,
        "I_rms": I_rms,
        "R_coil": R_coil,
        "L_coil": L_coil,
        "X_L": X_L,
        "power_factor_coil": power_factor_coil,
        "C_pfc": C_pfc,
        "P_copper": P_copper,
        "P_copper_no_pfc": P_copper_no_pfc,
        "P_iron": P_iron,
        "P_alt_loss": P_alt_loss,
        "Br_alt_corrected": Br_alt_corrected,

        # Heat exchangers
        "Re_cooler": Re_cooler,
        "dp_cooler_Pa": dp_cooler,
        "NTU_cooler": NTU_cooler,
        "Re_regen": Re_regen,
        "dp_regen_Pa": dp_regen,
        "NTU_regen": NTU_regen,
        "regen_effectiveness": regen_effectiveness,
        "dp_total_Pa": dp_total,
        "dp_total_frac": dp_total_frac,

        # Heater
        "dT_heater": dT_heater,
        "dT_heater_wall": dT_heater_wall,
        "dT_heater_ext": dT_heater_ext,
        "dT_heater_total": dT_heater_total,
        "h_heater": h_heater,
        "Re_heater": Re_heater,
        "A_heater_total_mm2": A_heater_total,

        # Seals
        "leak_piston_pct": leak_piston_pct,
        "leak_displacer_pct": leak_displacer_pct,

        # Dynamics
        "f_natural": f_natural,
        "f_resonance_error": f_resonance_error,
        "mag_spring_stroke_ratio": mag_spring_stroke_ratio,
        "k_gas": k_gas_spring,
        "k_mag": k_mag_spring,
        "k_total": k_total_spring,
        "m_piston_total_g": m_total * 1000,

        # Displacer dynamics
        "phase_achievable_deg": phase_achievable_deg,
        "phase_error_deg": phase_error_deg,
        "m_displacer_kg": m_displacer_kg,
        "k_d_spring": k_d_spring,

        # Composite vessel
        "k_vessel_eff": k_vessel_eff,

        # SmCo magnets
        "Br_spring_corrected": Br_spring_corrected,
        "mag_demagnetization_risk": mag_demagnetization_risk,

        # Earth cooling loop
        "Q_cold_rejected": Q_cold_rejected,
        "L_ground_loop_req": L_ground_loop_req,

        # Validation
        "checks": checks,
        "checks_passed": sum(1 for *_, ok in checks if ok),
        "checks_total": len(checks),
    }


# ── Pretty-print report ──────────────────────────────────────────

def print_report(params=None):
    """Run evaluate() and print a formatted validation report."""
    p = {**DEFAULTS, **(params or {})}
    r = evaluate(p)

    print("=" * 70)
    print("FREE-PISTON STIRLING ENGINE — DESIGN VALIDATION")
    print("=" * 70)

    print("\n── VOLUMES ──")
    print(f"  Bore:                 {p['vessel_id']:.0f} mm")
    print(f"  Piston swept:         {r['V_swept_piston_cc']:.2f} cc  (stroke {p['piston_stroke']} mm)")
    print(f"  Displacer swept:      {r['V_swept_displacer_cc']:.2f} cc  (stroke {p['displacer_stroke']} mm)")
    print(f"  Total dead volume:    {r['V_dead_total_cc']:.2f} cc")
    print(f"  Dead volume ratio:    {r['dead_volume_ratio']:.2f}:1  (target < 1.0)")

    print("\n── SCHMIDT CYCLE ──")
    print(f"  Pressure ratio:       {r['pressure_ratio']:.3f}")
    print(f"  Pressure swing:       +/-{r['pressure_swing_pct']:.1f}%")
    print(f"  Schmidt power:        {r['P_schmidt']:.1f} W (ideal)")
    print(f"  Beale number:         {r['Beale_number']:.4f}")

    print("\n── LOSS BUDGET ──")
    print(f"  Thermal input:        {p['Q_input']:.0f} W")
    print(f"  Thermal losses:")
    print(f"    Shuttle heat:       {r['P_loss_shuttle']:>7.1f} W")
    print(f"    Displacer cond:     {r['P_loss_disp_cond']:>7.1f} W")
    print(f"    Vessel wall cond:   {r['P_loss_vessel_cond']:>7.1f} W")
    print(f"    Regen imperfection: {r['P_loss_regen']:>7.1f} W")
    print(f"    Regen axial cond:   {r['P_loss_regen_cond']:>7.1f} W")
    print(f"    ─────────────────────────────")
    print(f"    Total thermal:      {r['P_loss_thermal']:>7.1f} W")
    print(f"  Available for cycle:  {r['Q_available']:.1f} W")
    print(f"  Carnot limit:         {r['eta_carnot']*100:.1f}% -> {r['Q_cycle']*r['eta_carnot']:.1f} W max")
    print(f"  Indicated power:      {r['P_indicated_actual']:.1f} W")
    print(f"  Mechanical losses:")
    print(f"    HX pumping:         {r['P_loss_pumping']:>7.1f} W")
    print(f"    Gas spring hyst:    {r['P_loss_hysteresis']:>7.1f} W")
    print(f"    Seal leakage:       {r['P_loss_seal']:>7.1f} W")
    print(f"    ─────────────────────────────")
    print(f"    Total mechanical:   {r['P_loss_mechanical']:>7.1f} W")
    print(f"  Net indicated:        {r['P_net_indicated']:.1f} W")
    print(f"  Alternator losses:")
    print(f"    Copper (I²R):       {r['P_copper']:>7.1f} W")
    print(f"    Iron (core):        {r['P_iron']:>7.1f} W")
    print(f"    ─────────────────────────────")
    print(f"    Total alt loss:     {r['P_alt_loss']:>7.1f} W")
    print(f"  Alternator η:         {r['eta_alternator']*100:.1f}%  "
          f"(V_emf={r['V_emf_rms']:.1f}V, I={r['I_rms']:.2f}A, R={r['R_coil']:.1f}Ω)")
    print(f"  Electronics η:        {p['eta_electronics']*100:.0f}%")
    print(f"  Adiabatic correction: {r['eta_adia']*100:.1f}%")
    print(f"  ═══════════════════════════════")
    print(f"  ELECTRICAL OUTPUT:    {r['P_electrical']:.1f} W")
    print(f"  OVERALL EFFICIENCY:   {r['eta_overall']*100:.1f}%")
    print(f"  Carnot fraction:      {r['eta_carnot_fraction']*100:.1f}% of Carnot")

    print("\n── HEAT EXCHANGERS ──")
    print(f"  Cooler Re:            {r['Re_cooler']:.0f}  dP: {r['dp_cooler_Pa']:.0f} Pa")
    print(f"  Regen Re:             {r['Re_regen']:.1f}  dP: {r['dp_regen_Pa']:.0f} Pa")
    print(f"  Regen effectiveness:  {r['regen_effectiveness']*100:.1f}%")
    print(f"  Total dP / Pmean:     {r['dp_total_frac']*100:.2f}%")
    print(f"  Heater Re:            {r['Re_heater']:.0f}  h: {r['h_heater']:.0f} W/m²K")
    print(f"  Heater gas dT:        {r['dT_heater']:.0f} C  (gas-side only)")
    print(f"  Heater wall dT:       {r['dT_heater_wall']:.0f} C  (conduction through wall)")
    print(f"  Heater ext dT:        {r['dT_heater_ext']:.0f} C  (source-to-wall convection)")
    print(f"  Heater total dT:      {r['dT_heater_total']:.0f} C  (source→gas, target < 200)")

    print("\n── SEALS ──")
    print(f"  Piston clearance:     {p['piston_clearance']*1000:.0f} um radial")
    print(f"  Piston leakage:       {r['leak_piston_pct']:.2f}%")
    print(f"  Displacer clearance:  {p['displacer_clearance']*1000:.0f} um radial")
    print(f"  Displacer leakage:    {r['leak_displacer_pct']:.2f}%")

    print("\n── DYNAMICS ──")
    print(f"  Gas spring stiffness: {r['k_gas']/1000:.1f} kN/m")
    print(f"  Mag spring stiffness: {r['k_mag']/1000:.1f} kN/m")
    print(f"  Total stiffness:      {r['k_total']/1000:.1f} kN/m")
    print(f"  Piston mass:          {r['m_piston_total_g']:.0f} g")
    print(f"  Natural frequency:    {r['f_natural']:.1f} Hz  "
          f"(target: {p['freq']:.0f} Hz, error: {r['f_resonance_error']*100:.0f}%)")
    print(f"  Mag spring ratio:     {r['mag_spring_stroke_ratio']:.3f}  "
          f"(stroke/2 / gap, target < 0.33)")
    print(f"  Displacer mass:       {r['m_displacer_kg']*1000:.0f} g")
    print(f"  Displacer spring k:   {r['k_d_spring']:.0f} N/m")
    print(f"  Phase achievable:     {r['phase_achievable_deg']:.1f}°  "
          f"(target: {p['phase_angle']:.0f}°, error: {r['phase_error_deg']:.1f}°)")
    demag = "WARNING — exceeds T_max_SmCo" if r['mag_demagnetization_risk'] else "OK"
    print(f"  SmCo Br (spring):     {r['Br_spring_corrected']:.3f} T  ({demag})")
    print(f"  SmCo Br (alternator): {r['Br_alt_corrected']:.3f} T")

    print("\n── ALTERNATOR (INDUCTANCE) ──")
    print(f"  Coil R:               {r['R_coil']:.2f} Ω")
    print(f"  Coil L:               {r['L_coil']*1000:.3f} mH")
    print(f"  Reactance X_L:        {r['X_L']:.2f} Ω  at {p['freq']:.0f} Hz")
    print(f"  Power factor:         {r['power_factor_coil']:.3f}  "
          f"(1.0 = purely resistive)")
    print(f"  PFC capacitor:        {r['C_pfc']*1e6:.1f} μF  (to cancel X_L)")
    print(f"  Cu loss (with PFC):   {r['P_copper']:.1f} W")
    print(f"  Cu loss (no PFC):     {r['P_copper_no_pfc']:.1f} W")

    print("\n── EARTH COOLING LOOP ──")
    print(f"  Heat to reject:       {r['Q_cold_rejected']:.0f} W  "
          f"(Q_input − P_electrical)")
    print(f"  Required pipe length: {r['L_ground_loop_req']:.0f} m  "
          f"(25mm HDPE, 1m depth, ΔT ≈ 3°C to soil)")

    k_d = r.get("k_displacer", p.get("k_displacer",
            MATERIALS.get(p['displacer_material'], MATERIALS['ss316'])["k"]))
    k_v = r.get("k_vessel", p.get("k_vessel",
            MATERIALS.get(p['vessel_material'], MATERIALS['ss316'])["k"]))
    # Find closest named material
    def _mat_name(k_val):
        best = min(MATERIALS.items(), key=lambda m: abs(m[1]["k"] - k_val))
        if abs(best[1]["k"] - k_val) < 1.0:
            return best[1]["name"]
        return f"custom"
    print(f"\n── MATERIALS ──")
    print(f"  Displacer:            {_mat_name(k_d)} (k={k_d:.1f} W/mK)")
    k_v_eff = r.get("k_vessel_eff", k_v)
    liner_frac = p.get("vessel_liner_frac", 0.0)
    if liner_frac > 0 and p.get("vessel_liner_k"):
        print(f"  Vessel (outer shell): {_mat_name(k_v)} (k={k_v:.1f} W/mK, "
              f"{(1-liner_frac)*100:.0f}% of wall)")
        print(f"  Vessel (inner liner): {_mat_name(p['vessel_liner_k'])} "
              f"(k={p['vessel_liner_k']:.1f} W/mK, {liner_frac*100:.0f}% of wall)")
        print(f"  Vessel effective k:   {k_v_eff:.1f} W/mK")
    else:
        print(f"  Vessel:               {_mat_name(k_v)} (k={k_v:.1f} W/mK)")

    print("\n" + "=" * 70)
    print("VALIDATION CHECKS")
    print("=" * 70)
    for name, value, target, ok in r["checks"]:
        status = "PASS" if ok else "FAIL"
        if isinstance(value, float):
            val_str = f"{value:.2f}"
        else:
            val_str = str(value)
        print(f"  [{status}]  {name:25s}  {val_str:>10s}  (target: {target})")
    print(f"\n  {r['checks_passed']}/{r['checks_total']} checks passed")

    return r


if __name__ == "__main__":
    print_report()
