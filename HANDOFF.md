# Handoff Document

## Goal

Design and build a solar thermal power generator with cascade conversion (Stirling -> ORC -> TEG), sand battery storage, and parabolic dish collector. Target 30% solar-to-electric efficiency using only non-toxic, commonly available materials.

## Current Progress

### This Session — Free-Piston Stirling Engine & System Architecture

1. **Earth cooling loop added** to system architecture (`docs/design/system-architecture.md`)
   - Ground heat sink at 1.5-2m depth (~10-15°C year-round) for TEG cold side
   - Dual-use design: diverter valve routes coolant to water tank when needed, earth loop when tank is satisfied
   - Boosts TEG output ~2x by lowering cold side from 40°C to ~15°C

2. **Free-piston Stirling engine redesigned** (`cad/stirling/free_piston_stirling.py`)
   - Replaced mechanical flexure springs with magnetic springs (opposing NdFeB ring magnets)
   - Removed displacer rod — moving magnet ring bonds directly to displacer bottom
   - Wall-mounted magnetic spring rings (vessel wall + displacer outer edge) to keep center bore open for gas flow
   - Magnet ring bonded concentrically around power piston (not stacked on top)
   - Sealed pressure vessel top with bore for heater head
   - Added centering magnet on vessel floor to hold piston at rest (repels existing alternator magnet ring)

3. **Cross-section export script** (`cad/stirling/cross_section.py`)
   - Generates half-section views: STEP (colored), SVG (2D line drawing), STL
   - Cuts all components along XZ plane for internal visibility

4. **Documentation updated**
   - `docs/research/heat-conversion.md` — Full free-piston design description with component layout, operating cycle, and design rationale
   - `docs/design/system-architecture.md` — Earth cooling loop diagram and sizing section

### Prior Sessions (from git history)

- Parabolic dish collector CAD (1m dish, 8 petals, receiver, assembly)
- Gamma-type Stirling engine CAD
- Efficiency targets documentation (path from 18% to 30%)
- ReflecTech mirror film research
- Hex and octagon+square faceted dish variants

## What Worked

- **CadQuery** for parametric CAD — `pip install cadquery` works fine, use `cq.Assembly` for multi-part models, `.save()` for STEP export
- **Iterative design review** — building the CAD, viewing the cross-section, and catching issues (unsealed vessel, disconnected piston/magnet, gas flow blockage) led to significant design improvements
- **STEP files** for 3D viewing — colored assemblies viewable in FreeCAD or any STEP viewer
- **SVG export** via CadQuery's `cq.exporters.export()` with `projectionDir` option for 2D drawings

## What Didn't Work

- **OCP CAD Viewer VS Code extension** — user couldn't get it to render. Fell back to opening STEP files directly.
- **`code` command** opens Cursor (user's `code` is mapped to Cursor). Use `open -a "Visual Studio Code" <file>` instead.
- **Boolean union of coincident faces** fails in CadQuery — use `cq.Assembly` or single revolve instead (noted in memory)
- **Bore-spanning magnetic springs** — original design had magnet rings filling nearly the entire vessel bore diameter, blocking gas flow. Redesigned to wall-mounted rings.

## Next Steps

### Immediate

- **Regenerator** — not yet modeled in the free-piston Stirling. Needs a mesh/matrix between hot and cold zones. Critical for efficiency (recovers 90-95% of heat each cycle).
- **Gas flow paths** — the current model shows the basic layout but doesn't model the actual flow channels between hot space, regenerator, cooler, and compression space.
- **Heater head internal fins** — the external fins are modeled but internal heat transfer surfaces (to the helium) are not.

### Design Validation

- **Resonant frequency calculation** — verify that piston mass, bounce space volume, and magnetic spring stiffness produce a viable operating frequency
- **Magnetic spring force modeling** — calculate repulsive force vs. displacement curve for the wall-mounted ring geometry
- **Thermal analysis** — ensure magnets stay below NdFeB Curie temperature (~150°C) in their positions

### Other Components (Not Yet Started)

- **ORC stage** — scroll expander or Tesla turbine, working fluid selection
- **TEG stage** — module selection, heat exchanger design
- **Sand battery** — insulated container, heat extraction mechanism
- **Earth cooling loop** — ground loop sizing calculations
- **System integration** — plumbing, controls, electrical output conditioning

## Key Files

| File | Description |
|------|-------------|
| `cad/stirling/free_piston_stirling.py` | Free-piston Stirling CAD (target architecture) |
| `cad/stirling/gamma_stirling.py` | Gamma-type Stirling CAD (simpler design) |
| `cad/stirling/cross_section.py` | Cross-section export script |
| `cad/collector/dish.py` | Parabolic dish CAD |
| `cad/collector/receiver.py` | Cavity receiver CAD |
| `docs/research/heat-conversion.md` | Conversion research + free-piston design docs |
| `docs/design/system-architecture.md` | System diagram + earth cooling loop |
| `docs/design/efficiency-targets.md` | Path from 18% to 30% efficiency |
