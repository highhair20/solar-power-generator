# Efficiency Optimization Targets

## Objective

Achieve **30% overall solar-to-electric efficiency**, up from the current ~18% baseline. This would match the best commercial dish-Stirling CSP systems.

---

## Current vs Target Efficiency Chain

| Stage | Current | Target | Improvement Strategy |
|---|---|---|---|
| **Mirror reflectance** | 90% | 95% | Silver-on-glass or dielectric-coated aluminum |
| **Optical intercept** | 95% | 97% | Tighter surface accuracy (<1mm RMS), tracking ±0.05° |
| **Blocking/shadowing** | 98% | 99% | Thinner support arms, offset receiver mount |
| **Optical subtotal** | **84%** | **91%** | |
| **Receiver absorptance** | 95% | 97% | Solar selective coating (Pyromark 2500 or cermet) |
| **Radiation loss** | 10% | 5% | Quartz glass window over aperture |
| **Convection + conduction** | 7% | 4% | Vacuum gap or better ceramic insulation |
| **Receiver subtotal** | **~83%** | **~90%** | |
| **Storage** | ~95% | ~97% | Thicker insulation, smaller surface-to-volume ratio |
| **Stirling engine** | 15-25% | 30-35% | Free-piston design, pressurized helium, precision regenerator |
| **ORC recovery** | 10-15% | 12-15% | Captures Stirling waste heat at 300°C |
| **TEG recovery** | 3-5% | 4-5% | Captures ORC waste heat at 100°C |
| **Cascade conversion subtotal** | **~27%** | **~38%** | |

### Overall

- **Current:** 0.84 × 0.83 × 0.95 × 0.27 = **~18%**
- **Target:** 0.91 × 0.90 × 0.97 × 0.38 = **~30.4%**

---

## Biggest Levers (ranked by impact)

1. **Stirling engine 20% → 32%** — ~8 points of system efficiency. Free-piston with pressurized helium (proven by Infinia, Qnergy). Hardest but most rewarding.
2. **Aperture window (radiation loss 10% → 5%)** — fused quartz disc over receiver aperture. ~3 points of system efficiency.
3. **Mirror reflectance 90% → 95%** — silver-on-glass mirrors or ReflecTech mirror film (~94%, self-adhesive, NREL-tested). ~2 points. Film is lighter and easier to apply; glass gives highest reflectance but is heavier and fragile.
4. **Selective absorber coating** — commercial CSP receiver coatings. ~1 point. Drop-in improvement.

Levers 1+2 alone: 18% → ~25%.
All four: 18% → ~30%.

---

## Context: Industry Comparison

| Technology | Efficiency |
|---|---|
| Solar thermal (large CSP, dish-Stirling) | 25-30% |
| Solar PV (rooftop) | 18-22% |
| Solar thermal (this project, current) | ~18% |
| Solar thermal (this project, target) | **30%** |

The 30% target matches the best dish-Stirling CSP systems (Infinia, Stirling Energy Systems) before the technology was abandoned in favor of cheaper but less efficient PV. Those systems used professional free-piston Stirling engines with pressurized helium — the same architecture targeted here.

---

## Prototype Strategy

A 24" (610mm) Edmund Optics dish can serve as a test platform:

| | 24" Prototype | 1m Full System |
|---|---|---|
| Aperture area | 0.292 m² | 0.785 m² |
| Solar input | 292 W | 785 W |
| Thermal output | ~210 W | ~550 W |
| Electrical (at 18%) | ~37 W | ~140 W |
| Electrical (at 30%) | ~62 W | ~235 W |

Thermal output scales linearly with area (2.7x from 24" to 1m). Electrical output scales slightly better (~3-3.5x) because conversion efficiency improves with scale.

---

## Design Constraints (unchanged)

- **No toxic or exotic materials** — all materials non-toxic and commonly available
- **Green to build** — minimal environmental impact in manufacturing
- **Maximum efficiency** — optimize collection, storage, and conversion

These constraints are a key differentiator vs PV panels, which contain lead (solder), cadmium (thin-film), and use hydrofluoric acid in manufacturing.
