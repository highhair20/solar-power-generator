# Handoff Document

## Goal

Design and build a solar thermal power generator with cascade conversion (Stirling → ORC → TEG), sand battery storage, and parabolic dish collector. Target 30% solar-to-electric efficiency using only non-toxic, commonly available materials.

## Current Progress

### Most Recent Work (uncommitted) — Internal Heat Exchangers

Significant updates to `cad/stirling/free_piston_stirling.py` and `cad/stirling/cross_section.py`:

1. **Regenerator added** — annular mesh housing (IR 38mm, OR 44mm, 18mm long) with 16 flow holes. Sits between cooler and displacer (Z 140–158). Recovers 90-95% of heat each cycle — critical for efficiency.

2. **Internal cooler added** — annular tube bank lining the vessel wall (IR 38mm, OR 44mm, 38mm long) with 12 axial flow holes. Gas flows through tubes, heat transfers radially to vessel wall where external fins dissipate it.

3. **Gas flow path now defined** — components are laid out in thermodynamic order bottom-to-top:
   - Bounce space (Z 0–40) → Power piston (Z 40) → Alternator (Z 58) → Magnetic spring fixed (Z 76) → Magnetic spring moving (Z 94) → Internal cooler (Z 102–140) → Regenerator (Z 140–158) → Displacer (Z 160) → Hot space → Heater head (Z 250)

4. **Heater head OD corrected** to match vessel bore (acts as cap on vessel).

5. **Displacer clearance tightened** from 4mm to 1.5mm total (0.75mm radial) for better sealing.

6. **External cooler fins repositioned** to align with internal cooler zone.

7. **Cross-section script updated** to include internal cooler and regenerator in both STEP and SVG exports.

### Also Uncommitted

- `cad/stirling/README.md` — documentation for Stirling CAD scripts
- `cad/stirling/analysis.py` — analysis/calculation script
- `cad/stirling/output/` — generated output files
- `MIRO-SUN reflective 90 weatherproof_EN.pdf` — mirror film datasheet

### Prior Sessions (committed)

- **Free-piston Stirling engine** — sealed pressure vessel with magnetic springs (wall-mounted opposing NdFeB ring magnets), linear alternator, centering magnet, no connecting rod
- **Earth cooling loop** added to system architecture for TEG cold side (~10-15°C)
- **Parabolic dish collector CAD** (1m dish, 8 petals, receiver, assembly)
- **Gamma-type Stirling engine** CAD (simpler alternative design)
- **Efficiency targets** documented (path from 18% to 30%)
- **ReflecTech mirror film** research, hex/octagon faceted dish variants

## What Worked

- **CadQuery** for parametric CAD — `pip install cadquery`, use `cq.Assembly` for multi-part models, `.save()` for STEP export
- **Iterative cross-section review** — building CAD, viewing the cross-section, catching issues (unsealed vessel, blocked gas flow, disconnected components) led to significant improvements
- **STEP files** for 3D viewing in FreeCAD or any STEP viewer
- **SVG export** via `cq.exporters.export()` with `projectionDir` for 2D drawings
- **Annular heat exchanger design** — keeping inner bore open for gas flow while packing heat exchange area in the annular gap near the vessel wall

## What Didn't Work

- **OCP CAD Viewer VS Code extension** — couldn't render. Use STEP files directly.
- **`code` command** opens Cursor (user's mapping). Use `open -a "Visual Studio Code" <file>` instead.
- **Boolean union of coincident faces** fails in CadQuery — use `cq.Assembly` or single revolve
- **Bore-spanning magnetic springs** — blocked gas flow. Redesigned to wall-mounted rings at vessel perimeter.

## Next Steps

### Immediate (Uncommitted Work to Review)

- **Review and commit** the regenerator/cooler changes — run `cross_section.py` to verify the new components render correctly in the cross-section
- **Verify gas flow clearance** — confirm there's adequate center bore open between internal cooler IR (38mm) and any central components

### Design Refinement

- **Heater head internal fins** — external fins modeled but internal heat transfer surfaces (to helium) are not
- **Regenerator mesh modeling** — current representation uses holes through a solid annulus; could add detail for actual mesh/screen packing
- **Seal design** — displacer and piston clearance seals need more thought (labyrinth seals? close-tolerance?)

### Design Validation

- **Resonant frequency calculation** — verify piston mass + bounce space volume + magnetic spring stiffness produce viable operating frequency (~30-60 Hz typical)
- **Magnetic spring force modeling** — repulsive force vs. displacement curve for wall-mounted ring geometry
- **Thermal analysis** — ensure NdFeB magnets stay below Curie temp (~150°C) in their positions
- **Pressure vessel stress** — verify wall thickness for 20-30 bar helium charge

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
| `cad/stirling/cross_section.py` | Cross-section export script |
| `cad/stirling/analysis.py` | Analysis/calculation script (new, uncommitted) |
| `cad/stirling/README.md` | Stirling CAD documentation (new, uncommitted) |
| `cad/stirling/gamma_stirling.py` | Gamma-type Stirling CAD (simpler design) |
| `cad/collector/dish.py` | Parabolic dish CAD |
| `cad/collector/receiver.py` | Cavity receiver CAD |
| `docs/research/heat-conversion.md` | Conversion research + free-piston design docs |
| `docs/design/system-architecture.md` | System diagram + earth cooling loop |
| `docs/design/efficiency-targets.md` | Path from 18% to 30% efficiency |
