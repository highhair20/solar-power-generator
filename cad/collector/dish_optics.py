"""
Parabolic Dish — Analytical Optical Model

Computes intercept factor, concentration ratio, and focal flux distribution
from first principles, replacing the fixed optical efficiency assumptions
in efficiency-targets.md.

Models:
1. Geometric concentration ratio (from dish geometry)
2. Intercept factor (fraction of reflected flux that enters receiver aperture)
3. Focal spot size distribution (Gaussian error model)
4. Optical efficiency chain (reflection × intercept × blocking)

The intercept factor uses a Gaussian angular error model (Jeter, 1986):
  - Slope error σ_s (surface irregularity, reflected at 2× angle)
  - Tracking error σ_t (drive/sensor accuracy)
  - Sunshape σ_sun (solar disc angular radius ≈ 4.65 mrad HWHM → σ ≈ 2.73 mrad)
  Total error: σ_total = sqrt((2σ_s)² + σ_t² + σ_sun²)

References:
- Jeter (1986) "Analytical Determination of the Optical Performance of
  Practical Parabolic Trough Collectors" Solar Energy 36(3)
- Duffie & Beckman "Solar Engineering of Thermal Processes" (4th ed., 2013)
- Rabl (1976) "Optical and Thermal Properties of Compound Parabolic
  Concentrators" Solar Energy 18(6)
"""

import math


SOLAR_DISC_SIGMA = 2.73e-3   # rad — Gaussian sigma of solar disc angular profile
                              # (half-angle 4.65 mrad → σ = 4.65/√(2 ln 2) ≈ 2.73 mrad)


DEFAULTS = {
    # Dish geometry
    "dish_diameter": 1.0,          # m — aperture diameter
    "rim_angle": 45.0,             # degrees — rim angle (45° → f/D = 0.60)

    # Reflector
    "reflectance": 0.94,           # solar-weighted reflectance (ReflecTech mirror film)
    "blocking_factor": 0.98,       # fraction unblocked by receiver support arms

    # Error sources (1-sigma angular errors)
    "sigma_slope": 2.0e-3,         # rad — surface slope error (1σ) — good DIY: 2-5 mrad
    "sigma_tracking": 0.87e-3,     # rad — tracking error (1σ) — 0.05° ≈ 0.87 mrad

    # Receiver aperture
    "aperture_diameter": 0.06,     # m — receiver aperture diameter
}


def focal_length(dish_diameter, rim_angle_deg):
    """Compute focal length from diameter and rim angle.

    For a paraboloid: f = D / (4 × tan(θ_rim / 2))

    Args:
        dish_diameter: m
        rim_angle_deg: degrees

    Returns:
        f: m — focal length
    """
    theta = math.radians(rim_angle_deg)
    return dish_diameter / (4 * math.tan(theta / 2))


def geometric_concentration(dish_diameter, rim_angle_deg, aperture_diameter):
    """Compute geometric concentration ratio C = A_dish / A_aperture.

    This is the maximum possible concentration (with perfect optics).
    The theoretical maximum for a 2D concentrator at the given rim angle:
        C_max = (sin(θ_rim) / sin(θ_sun))² / 4  (for paraboloid)

    But for practical sizing, we use: C = A_aperture_dish / A_aperture_receiver

    Args:
        dish_diameter: m
        rim_angle_deg: degrees (not used for simple area ratio, but included for
                       future use with optical efficiency correction)
        aperture_diameter: m — receiver aperture

    Returns:
        C: geometric concentration ratio (dimensionless suns)
    """
    A_dish = math.pi / 4 * dish_diameter**2
    A_aperture = math.pi / 4 * aperture_diameter**2
    return A_dish / A_aperture


def image_rms_size(dish_diameter, rim_angle_deg,
                   sigma_slope, sigma_tracking,
                   sigma_sunshape=SOLAR_DISC_SIGMA):
    """Compute the RMS image size at the focal plane.

    Each error source contributes independently (Gaussian, quadrature sum):
        σ_image = f × σ_total
        σ_total = sqrt((2σ_slope)² + σ_tracking² + σ_sunshape²)

    The factor of 2 on slope error: a surface error σ_s reflects the ray
    at 2σ_s from the specular direction (slope error doubles in reflection).

    Args:
        dish_diameter: m
        rim_angle_deg: degrees
        sigma_slope: rad — 1σ surface slope error
        sigma_tracking: rad — 1σ tracking error
        sigma_sunshape: rad — 1σ solar disc angular spread

    Returns:
        sigma_image: m — 1σ image radius at focal plane
        sigma_total: rad — total 1σ angular error
    """
    f = focal_length(dish_diameter, rim_angle_deg)
    sigma_total = math.sqrt((2 * sigma_slope)**2 + sigma_tracking**2 + sigma_sunshape**2)
    sigma_image = f * sigma_total
    return sigma_image, sigma_total


def intercept_factor(dish_diameter, rim_angle_deg, aperture_diameter,
                     sigma_slope, sigma_tracking,
                     sigma_sunshape=SOLAR_DISC_SIGMA):
    """Compute the intercept factor γ: fraction of reflected flux entering aperture.

    For a Gaussian image profile, the fraction within radius r_ap is:
        γ = 1 - exp(-r_ap² / (2 σ_image²))
    where r_ap = aperture_radius and σ_image = focal-plane image sigma.

    This is the complementary CDF of the 2D Gaussian (Rayleigh distribution):
        P(r < r_ap) = 1 - exp(-(r_ap/σ_image)²/2)

    Note: This formula assumes the image is centered on the aperture (perfect
    boresight), which requires the average pointing to be exact. The sigma
    errors represent random scatter around the mean pointing direction.

    Args:
        dish_diameter, rim_angle_deg, aperture_diameter: geometry
        sigma_slope, sigma_tracking: error sources (rad, 1σ)
        sigma_sunshape: solar disc sigma (rad)

    Returns:
        gamma: intercept factor (0–1)
        sigma_image: m — 1σ image radius at focal plane
    """
    r_ap = aperture_diameter / 2
    sigma_image, _ = image_rms_size(dish_diameter, rim_angle_deg,
                                    sigma_slope, sigma_tracking, sigma_sunshape)

    if sigma_image <= 0:
        return 1.0, 0.0

    # Fraction of 2D Gaussian within circle of radius r_ap
    gamma = 1.0 - math.exp(-r_ap**2 / (2 * sigma_image**2))
    return gamma, sigma_image


def evaluate(params=None):
    """Compute full optical efficiency chain from first principles.

    Args:
        params: dict of design parameters (missing keys use DEFAULTS)

    Returns:
        dict with all computed metrics
    """
    p = {**DEFAULTS, **(params or {})}

    D = p["dish_diameter"]
    theta_rim = p["rim_angle"]
    d_ap = p["aperture_diameter"]
    rho = p["reflectance"]
    f_block = p["blocking_factor"]
    sigma_s = p["sigma_slope"]
    sigma_t = p["sigma_tracking"]

    f = focal_length(D, theta_rim)
    A_dish = math.pi / 4 * D**2
    A_aperture = math.pi / 4 * d_ap**2
    C_geom = A_dish / A_aperture

    gamma, sigma_image = intercept_factor(D, theta_rim, d_ap, sigma_s, sigma_t)

    # Total angular error budget
    _, sigma_total = image_rms_size(D, theta_rim, sigma_s, sigma_t)

    # Optical efficiency chain
    eta_reflection = rho
    eta_intercept = gamma
    eta_blocking = f_block
    eta_optical = eta_reflection * eta_intercept * eta_blocking

    # Peak concentration at aperture (flux at focal spot center, normalized to DNI)
    # For a 2D Gaussian: peak flux = total power / (2π σ²)
    # C_peak = C_geom × rho × f_block / (2π σ_norm²)  where σ_norm = σ_image / r_ap
    sigma_norm = sigma_image / (d_ap / 2) if d_ap > 0 else 1e6
    C_peak = C_geom * rho * f_block / (2 * math.pi * sigma_norm**2) if sigma_norm > 0 else 0

    # Mean concentration within aperture (= C_geom × η_optical)
    C_mean = C_geom * eta_optical

    # Spot size metrics
    d_90pct = 2 * sigma_image * math.sqrt(2 * math.log(10))  # diameter containing 90%
    d_95pct = 2 * sigma_image * math.sqrt(2 * math.log(20))  # diameter containing 95%

    return {
        # Geometry
        "focal_length": f,
        "f_over_D": f / D,
        "A_dish_m2": A_dish,
        "A_aperture_m2": A_aperture,

        # Errors
        "sigma_slope_mrad": sigma_s * 1e3,
        "sigma_tracking_mrad": sigma_t * 1e3,
        "sigma_sunshape_mrad": SOLAR_DISC_SIGMA * 1e3,
        "sigma_total_mrad": sigma_total * 1e3,
        "sigma_image_mm": sigma_image * 1e3,

        # Spot size
        "d_90pct_mm": d_90pct * 1e3,
        "d_95pct_mm": d_95pct * 1e3,

        # Optical efficiency chain
        "eta_reflection": eta_reflection,
        "eta_intercept": gamma,
        "eta_blocking": eta_blocking,
        "eta_optical": eta_optical,

        # Concentration
        "C_geometric": C_geom,
        "C_mean": C_mean,
        "C_peak": C_peak,
    }


def print_report(params=None):
    """Run evaluate() and print a formatted report."""
    p = {**DEFAULTS, **(params or {})}
    r = evaluate(p)

    print("=" * 60)
    print("PARABOLIC DISH — OPTICAL ANALYSIS")
    print("=" * 60)

    print(f"\n  Dish diameter:        {p['dish_diameter']*1000:.0f} mm")
    print(f"  Rim angle:            {p['rim_angle']:.0f}°")
    print(f"  Focal length:         {r['focal_length']*1000:.0f} mm  "
          f"(f/D = {r['f_over_D']:.2f})")
    print(f"  Aperture diameter:    {p['aperture_diameter']*1000:.0f} mm")

    print(f"\n── ANGULAR ERROR BUDGET ──")
    print(f"  Slope error (2×σ_s):  {2*p['sigma_slope']*1e3:.2f} mrad")
    print(f"  Tracking error:       {p['sigma_tracking']*1e3:.2f} mrad")
    print(f"  Sunshape (σ):         {SOLAR_DISC_SIGMA*1e3:.2f} mrad")
    print(f"  Total σ_total:        {r['sigma_total_mrad']:.2f} mrad")
    print(f"  Image 1σ radius:      {r['sigma_image_mm']:.1f} mm  at focal plane")
    print(f"  Spot d_90%:           {r['d_90pct_mm']:.1f} mm  (90% power contained)")
    print(f"  Spot d_95%:           {r['d_95pct_mm']:.1f} mm  (95% power contained)")

    print(f"\n── OPTICAL EFFICIENCY CHAIN ──")
    print(f"  Mirror reflectance:   {r['eta_reflection']*100:.1f}%")
    print(f"  Intercept factor:     {r['eta_intercept']*100:.1f}%")
    print(f"  Blocking/shadowing:   {r['eta_blocking']*100:.1f}%")
    print(f"  ─────────────────────────────")
    print(f"  OPTICAL EFFICIENCY:   {r['eta_optical']*100:.1f}%")

    print(f"\n── CONCENTRATION ──")
    print(f"  Geometric C:          {r['C_geometric']:.0f}×")
    print(f"  Mean C in aperture:   {r['C_mean']:.0f}×")
    print(f"  Peak C at center:     {r['C_peak']:.0f}×")
    print("=" * 60)
    return r


if __name__ == "__main__":
    print_report()

    # Sensitivity: show how intercept factor varies with aperture size and slope error
    print("\n── INTERCEPT FACTOR vs APERTURE DIAMETER ──")
    print(f"  (σ_slope = 2 mrad, σ_tracking = 0.87 mrad)")
    print(f"  {'d_ap (mm)':>10}  {'γ (%)':>6}  {'η_opt (%)':>9}  {'C_mean':>7}")
    for d_mm in [40, 50, 60, 70, 80, 100, 120]:
        r = evaluate({"aperture_diameter": d_mm / 1000})
        print(f"  {d_mm:>10}  {r['eta_intercept']*100:>6.1f}  "
              f"{r['eta_optical']*100:>9.1f}  {r['C_mean']:>7.0f}")

    print(f"\n── INTERCEPT FACTOR vs SLOPE ERROR (d_ap = 60 mm) ──")
    print(f"  {'σ_slope (mrad)':>15}  {'γ (%)':>6}  {'η_opt (%)':>9}  "
          f"{'spot d_90% (mm)':>15}")
    for s_mrad in [1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0]:
        r = evaluate({"sigma_slope": s_mrad * 1e-3, "aperture_diameter": 0.06})
        print(f"  {s_mrad:>15.1f}  {r['eta_intercept']*100:>6.1f}  "
              f"{r['eta_optical']*100:>9.1f}  {r['d_90pct_mm']:>15.1f}")
