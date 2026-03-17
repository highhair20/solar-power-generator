# Handoff Document

## Goal

Design and build a solar thermal power generator using a free-piston Stirling engine with direct-to-earth cooling. Target: maximize solar-to-electric efficiency using only non-toxic, commonly available materials. Current best: **205W at 37.4% efficiency** from a 1m parabolic dish (550W thermal input).

The system architecture has been simplified from the original cascade (Stirling → ORC → TEG) to **Stirling only with earth cooling** (T_cold = 15°C). Analysis showed the direct-to-earth approach produces nearly the same electrical output (205W vs ~144W cascade) with far less complexity, because the higher Carnot limit (67% vs 34%) more than compensates for losing the ORC and TEG stages.

## Current Progress

### Most Recent Work — First-Principles Physics Model

Built a complete computational engineering loop (Leap71-style): `analysis.py` computes engine performance from geometry → `optimize.py` searches the design space with NSGA-II → best parameters feed back into CAD.

**The physics model (`analysis.py`) uses zero empirical efficiency assumptions.** Nine items that previously relied on correlations from existing engines or flat assumptions were replaced with first-principles derivations:

1. **Adiabatic-corrected cycle** — Schmidt (isothermal) baseline × NTU-based correction for finite heat transfer in working spaces. Uses Annand correlation Nu = 0.75 Re^0.7 in both hot and cold spaces. This is the dominant loss: only 42% of ideal isothermal work is achieved.

2. **Temperature-dependent helium** — μ(T) = μ_ref(T/T_ref)^0.67, k(T) = k_ref(T/T_ref)^0.67 from Chapman-Enskog kinetic theory. Hot-side viscosity is ~1.8× cold-side.

3. **Heater HTC from fin channel flow** — Hydraulic diameter of inter-fin passages, Re, Nu from Shah & London developing flow correlation. Replaces flat h=150 W/m²K.

4. **Alternator electromagnetic model** — Faraday EMF (V = NωBA), copper I²R with temperature-corrected resistivity, Steinmetz iron losses. Computes V_emf, I, R_coil, η_alt from coil/magnet geometry.

5. **Oscillating flow friction (cooler)** — Zhao & Cheng correction: f_osc = f_steady × (1 + 0.25√(Va/Re)).

6. **Oscillating flow regen correlations** — Kinetic Reynolds number Re_ω corrects both friction (Gedeon & Wood) and Nusselt (Ibrahim et al.) for packed screens.

7. **Lee's gas spring hysteresis** — Exact analytical f(λ) = [sinh(2λ)-sin(2λ)]/[2λ(cosh(2λ)+cos(2λ))]. Correctly goes to zero in both isothermal and adiabatic limits.

8. **Material-aware densities** — Piston mass from MATERIALS table, SmCo magnet density (8400 kg/m³).

9. **Magnetic spring model** — Dipole-dipole repulsion: k = 12μ₀m²/(2πz⁵) per pair, stacked with gas spring for total resonant frequency.

### Optimizer Results (Best Design)

```
205W electrical @ 37.4% overall efficiency
Loss waterfall:
  550W input → -135W thermal losses → 415W available
  × 67% Carnot → 278W → × 42% adiabatic → 278W indicated
  - 35W mechanical → - 27W alternator → × 95% electronics → 205W
```

Key optimized parameters:
- 20mm piston stroke, 7.4mm displacer stroke
- 46 Hz, 11 bar helium
- 90° phase angle
- Ceramic vessel + displacer (k ≈ 2 W/mK)
- 0.8mm displacer wall, 76mm displacer length
- 23 heater fins (28mm × 37mm)
- 10-15 μm clearance seals
- 15mm regenerator, 0.60 porosity
- Dead volume ratio: 0.66

### CAD Model (earlier work, committed + uncommitted)

- Free-piston Stirling with helium fill tube, internal cooler, regenerator, heater head with external fins
- Linear alternator (moving magnet ring through coil)
- Wall-mounted SmCo magnetic springs
- Cross-section export script for review
- Gas flow path: bounce space → piston → alternator → cooler → regen → displacer → hot space → heater

### Other Components (committed)

- 1m parabolic dish CAD (8 petals, receiver, assembly)
- Gamma-type Stirling (simpler alternative, not the target design)
- System architecture docs, efficiency targets, materials research

## What Worked

- **Leap71-style computational loop** — Parameters → Physics → Score → Optimize → Better parameters. pymoo NSGA-II with 23 design variables, 2 objectives, 7 constraints finds good designs in 100-200 generations.
- **First-principles losses** — Each loss responds to geometry changes, so the optimizer can attack them. The fixed "50% of Carnot" assumption was a dead end — optimizer couldn't improve efficiency.
- **Material conductivity as a continuous design variable** — k_displacer and k_vessel as floats [2, 16] W/mK. Optimizer consistently picks ceramic (k≈2). Map back to real materials after.
- **CadQuery** for parametric CAD — `cq.Assembly` for multi-part models, `.save()` for STEP
- **Iterative cross-section review** for catching CAD issues
- **Annular HX design** — inner bore open for gas flow, heat exchange near vessel wall
- **Direct-to-earth cooling** instead of cascade — simpler, nearly same power output

## What Didn't Work

- **Fixed Carnot fraction** (eta_carnot_fraction = 0.50) — All optimizer runs produced identical efficiency regardless of geometry. The optimizer can only improve what the physics model exposes as variable.
- **Piston clearance as OD difference** — Initial model used piston_od = vessel_id - 1mm (0.5mm radial gap), giving 13,254% leakage. Real clearance seals are 15-50 μm radial. Fixed by adding explicit piston_clearance/displacer_clearance parameters.
- **Schmidt power without heat budget** — Produced 5664W from 550W input. Must cap indicated power at Q_available × η_Carnot.
- **Regen m_dot from piston bore × velocity** — Overestimated regen heat load by 3-5×. The regen mass flow is driven by the displacer, at mean-temperature density, and per-half-cycle mass = m_dot_peak/(π×freq).
- **Lee hysteresis without 1/(2λ) normalization** — Gave 1053W loss instead of 1.9W. The function f(λ) must decay as 1/(2λ) at large λ (adiabatic limit).
- **OCP CAD Viewer** — doesn't render. Use STEP files in FreeCAD.
- **`code` command** opens Cursor. Use `open -a "Visual Studio Code" <file>`.
- **Boolean union of coincident faces** in CadQuery — use Assembly or single revolve.
- **Bore-spanning magnetic springs** — blocked gas flow. Redesigned to wall-mounted rings.

## Next Steps

### Immediate

- **Commit all uncommitted work** — analysis.py, optimize.py, free_piston_stirling.py changes, cross_section.py, README.md, output files
- **Run longer optimization** (200 gen, 200 pop) with the full first-principles model to see if it converges higher than 37.4%
- **Add alternator coil parameters to optimizer design variables** — coil_turns, coil_wire_dia, coil_layers are currently fixed; the optimizer could reduce copper losses

### Model Improvements

- **Ceramic pressure vessel feasibility** — The optimizer picks k=2 (ceramic) for everything. Real ceramic pressure vessels at 11 bar are uncommon. Either constrain k ≥ 7 (titanium minimum) or model a composite vessel (ceramic liner + carbon fiber overwrap).
- **Frequency-resonance matching** — Natural frequency (73 Hz) is far from operating frequency (46 Hz). The optimizer doesn't penalize this mismatch. Add a constraint or soft penalty for |f_natural - freq|/freq.
- **Full adiabatic simulation** — The NTU-based correction is a linearization. A time-stepping nodal model (like Sage) would be more accurate but much more complex to implement.
- **Magnetic spring nonlinearity** — Dipole model is linear (valid near equilibrium). Real force curve is highly nonlinear. Matters for large-amplitude stability.

### CAD Updates

- **Update CAD with optimized geometry** — The optimizer output includes a parameter mapping (`generate_cad_params()` in optimize.py) that prints values to copy into free_piston_stirling.py
- **Heater internal fins in CAD** — analysis.py models them but the CAD doesn't render them yet
- **Displacer wall thickness** — optimizer wants 0.8mm; current CAD has 1.5mm

### System Integration

- **Earth cooling loop sizing** — Ground loop length, pipe diameter, flow rate for rejecting ~280W at T_cold = 15°C
- **Power electronics** — Rectifier + inverter design for 205W at variable frequency (~46 Hz)
- **Pressure vessel stress analysis** — Wall thickness verification for 11 bar with ceramic/titanium
- **Sand battery** — Still in the design. Storage allows running loads when sun isn't shining.

## Key Files

| File | Description |
|------|-------------|
| `cad/stirling/analysis.py` | **First-principles thermodynamic model** — 9 loss mechanisms, all from physics |
| `cad/stirling/optimize.py` | **NSGA-II optimizer** — 23 design variables, 2 objectives, 7 constraints |
| `cad/stirling/free_piston_stirling.py` | Free-piston Stirling CAD (CadQuery) |
| `cad/stirling/cross_section.py` | Cross-section STEP + SVG export |
| `cad/stirling/README.md` | Stirling CAD documentation |
| `cad/collector/dish.py` | 1m parabolic dish CAD |
| `cad/collector/receiver.py` | Cavity receiver CAD |
| `cad/collector/assembly.py` | Dish + receiver assembly |
| `docs/research/heat-conversion.md` | Conversion research + free-piston design docs |
| `docs/design/system-architecture.md` | System diagram + earth cooling loop |
| `docs/design/efficiency-targets.md` | Path from 18% to 30% (now exceeding 30%) |

## Key Constants

- **Dish area**: 0.785 m² (1m diameter)
- **Solar flux**: 1000 W/m² × 0.90 mirror × 0.78 intercept = **550W thermal**
- **T_hot**: 600°C (873K) — heater head temperature
- **T_cold**: 15°C (288K) — earth cooling loop
- **Carnot limit**: 67.0%
- **Working fluid**: Helium (monatomic ideal gas, γ=5/3, R=2077 J/kgK)
- **Magnets**: SmCo (Br=1.05T, Curie temp ~750°C, safe near hot zone)
