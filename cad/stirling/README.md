# Stirling Engine CAD Models

Parametric CadQuery models of two Stirling engine configurations for the solar thermal power system. These are conceptual/dimensional models for visualizing architecture and layout — not manufacturing drawings.

Both engines are sized for ~200W electrical output from ~550W thermal input (1m parabolic dish).

## Files

### `gamma_stirling.py` — Gamma-Type Stirling Engine

Two separate cylinders (hot displacer + cold power) connected by a passage with regenerator housing. Mechanical output via crankshaft and flywheel. This is the simpler, DIY-friendly configuration.

**Key parameters:**

| Parameter | Value |
|-----------|-------|
| Hot cylinder bore | 80 mm |
| Hot cylinder length | 100 mm |
| Cold cylinder bore | 60 mm |
| Cold cylinder length | 80 mm |
| Connecting passage | 25 mm ID |
| Flywheel diameter | 150 mm |
| Cylinder offset | 100 mm |

**Functions:**
- `make_hot_cylinder()` — displacer cylinder + heater head with fins
- `make_cold_cylinder()` — power cylinder + cooler fins
- `make_displacer()` — lightweight hollow displacer piston + rod
- `make_power_piston()` — solid power piston + connecting rod
- `make_connecting_passage()` — tube with regenerator housing
- `make_crankshaft()` — crankshaft + flywheel (90° phase angle)
- `make_gamma_stirling()` — full `cq.Assembly`

### `free_piston_stirling.py` — Free-Piston Stirling Engine

Single sealed pressure vessel with no crankshaft. Displacer and power piston oscillate freely, with a linear alternator converting motion to electricity. This is the high-efficiency target architecture (Infinia/Qnergy style) for pressurized helium.

**Key parameters:**

| Parameter | Value |
|-----------|-------|
| Pressure vessel OD | 100 mm |
| Pressure vessel length | 250 mm |
| Wall thickness | 5 mm |
| Heater head diameter | 80 mm |
| Piston diameter | 70 mm |
| Magnet ring OD | 88 mm |
| Stator OD | 120 mm |

**Functions:**
- `make_pressure_vessel()` — main cylindrical housing
- `make_heater_head()` — hot-end cap with radial fins
- `make_displacer()` — free-floating displacer + rod
- `make_displacer_spring()` — resonance tuning flexure
- `make_power_piston()` — piston + magnet ring
- `make_alternator_stator()` — coil housing (external)
- `make_cooler()` — cold-end fin rings
- `make_free_piston_stirling()` — full `cq.Assembly`

## Usage

```bash
# Generate gamma-type Stirling
python cad/stirling/gamma_stirling.py

# Generate free-piston Stirling
python cad/stirling/free_piston_stirling.py
```

Output files are written to `cad/stirling/output/` (gitignored).

## Color Convention

| Color | Meaning |
|-------|---------|
| Firebrick/red | Hot-side components |
| Steelblue/blue | Cold-side components |
| Orange/goldenrod | Pistons/displacers |
| Gray | Structural / mechanical |
| Green | Springs / alternator |
