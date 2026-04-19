# Solar Collector — Subsystem CLAUDE.md

> Read the project-level CLAUDE.md first. This file adds solar-collector-specific context.

## Subsystem Purpose

The solar collector is a concentrating collector that tracks the sun and focuses
Direct Normal Irradiance (DNI) onto a receiver at the focal point. Its job is to
maximise the thermal power delivered to thermal storage at the highest practical
temperature, across all operating conditions.

The collector geometry is not yet finalised — candidates include parabolic dish,
Scheffler reflector, and linear Fresnel. All models must be geometry-agnostic where
possible, parameterised by aperture area, concentration ratio, and optical efficiency.

---

## Physics Model

### Key Equations

**Intercepted solar power:**
```
Q_solar = DNI × A_aperture × cos(θ_incidence)
```

**Thermal power delivered to receiver:**
```
Q_collector = Q_solar × η_optical × (1 - f_shading) × (1 - f_blocking)
```

**Receiver thermal losses (combined radiation + convection):**
```
Q_loss = ε_receiver × σ × A_receiver × (T_receiver⁴ - T_sky⁴)
       + h_conv × A_receiver × (T_receiver - T_amb)
```

**Net power to thermal storage:**
```
q_collector_W = Q_collector - Q_loss
```

**Concentration ratio:**
```
C = A_aperture / A_receiver
```
For a parabolic dish, C typically ranges from 500 to 3000.

---

## Design Parameters (to be filled in)

| Parameter                  | Symbol              | Value       | Unit   |
|----------------------------|---------------------|-------------|--------|
| Collector geometry         | —                   | TBD         | —      |
| Aperture diameter          | `D_aperture_m`      | TBD         | m      |
| Aperture area              | `A_aperture_m2`     | TBD         | m²     |
| Focal length               | `f_m`               | TBD         | m      |
| Rim angle                  | `phi_rim_deg`       | TBD         | °      |
| Receiver area              | `A_receiver_m2`     | TBD         | m²     |
| Concentration ratio        | `C`                 | TBD         | —      |
| Peak optical efficiency    | `eta_optical`       | TBD         | —      |
| Receiver emissivity        | `epsilon_r`         | TBD         | —      |
| Tracking accuracy          | `sigma_track_mrad`  | TBD         | mrad   |
| Design DNI                 | `DNI_design_W_m2`   | 850         | W/m²   |
| Design receiver temp       | `T_receiver_K`      | TBD         | K      |

---

## Outputs (Interface to Thermal Storage)

These variables must be computed and passed downstream — see project CLAUDE.md.

| Variable            | Description                              | Unit |
|---------------------|------------------------------------------|------|
| `q_collector_W`     | Net thermal power to thermal storage     | W    |
| `T_focal_K`         | Focal point / receiver temperature       | K    |
| `eta_collector`     | Overall collector efficiency (q/Q_solar) | —    |

---

## Directory Structure

```
solar-collector/
├── CLAUDE.md              ← This file
└── cad/                   ← CadQuery CAD scripts
    ├── dish.py            ← Parametric parabolic dish (8 petals)
    ├── receiver.py        ← Cavity receiver (steel shell, insulation, mounting flange)
    ├── assembly.py        ← Full collector assembly (dish + receiver at focal point)
    ├── export.py          ← Batch export to STEP/STL/DXF
    └── output/            ← Generated STEP/STL/DXF (gitignored)

Python source → src/solar_collector/
├── geometry.py            ← Parabola geometry, focal length, rim angle calcs
├── optical_model.py       ← Optical efficiency, intercept factor, spillage
├── receiver_model.py      ← Thermal loss model for the receiver cavity
└── tracking/              ← Sun position, tracking angles (uses pvlib)
```

---

## Modeling Guidance

**Optical model priority:**
Use the intercept factor (γ) approach for spillage losses. Do not ignore tracking
error — it is a significant loss term for high-concentration collectors.

**Receiver model:**
Model the receiver as a cavity with an aperture. Radiation losses dominate at
temperatures above ~600°C. Use the effective emissivity of the cavity, not the
surface emissivity of the walls alone.

**Tracking:**
Use `pvlib.solarposition` for sun position (azimuth, elevation). Two-axis tracking
means incidence angle θ ≈ 0° at all times — verify this in the model but do not
assume perfect tracking. Apply `sigma_track_mrad` as a Gaussian tracking error.

**Shading & blocking:**
For a single stand-alone collector, shading by the receiver support structure is
typically 1–3%. Use a fixed shading factor unless doing a detailed ray-trace.

---

## Validation Targets

| Condition              | Expected Output           | Source              |
|------------------------|---------------------------|---------------------|
| DNI = 850 W/m², on-sun | `q_collector_W` > TBD W   | Design requirement  |
| η_optical at design pt | 0.82–0.88 typical range   | Duffie & Beckman    |
| Q_loss / Q_solar       | < 10% at design temp      | Engineering judgment|

Claude should flag any result outside these ranges and ask before proceeding.

---

## Failure Modes to Check

- `DNI = 0` (night / cloudy): `q_collector_W` must return 0, not negative
- Very high receiver temperature: verify radiation loss doesn't exceed Q_collector
- Incidence angle > 90°: collector should be stowed, output = 0
- Concentration ratio < 100: warn — insufficient for high-temperature operation
