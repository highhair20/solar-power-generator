# System Architecture

## Overview

This document describes the overall system design, heat flow paths, and stage interconnections.

**Design target:** ~140 W peak electrical output
**Location:** US Southwest (~1000 W/m² peak DNI)
**Primary collector:** 1 m parabolic dish (0.785 m² aperture, ~550 W peak thermal output)

---

## System Diagram

```
                         [Sun]
                           |
                           v
        [1 m Parabolic Dish (0.785 m²)]
                           |
                           v
                   [Thermal Receiver]
                           |
                           v
              [Sand Battery: 500-600°C]
                           |
                    ║ ║ ║ ║ ║ ║           ← Sodium heat pipes (buried in sand)
                    ║ ║ ║ ║ ║ ║           ← vapor travels to heater head (~5°C drop)
                    ╚═╩═╩═╩═╩═╝
                           |
                    [Heat pipe manifold bonded to heater head]
                           |
                           v
    ┌──────────────────────────────────────────────────────────┐
    │  STAGE 1: STIRLING ENGINE                                │
    │  Temperature: 600→300°C                                  │
    │  Efficiency: 33-37% (first-principles model)             │
    │  Config: Free-piston, pressurized helium                 │
    │                                                          │
    │  [Hot End] ←── heat in ←── Heat pipe manifold            │
    │  [Cold End] ──→ heat out ──→ Stage 2                     │
    │       │                                                  │
    │       v                                                  │
    │  [Linear Alternator] ──→ AC/DC Output                    │
    └──────────────────────────────────────────────────────────┘
                           |
                           | (~300°C heat rejection)
                           v
    ┌──────────────────────────────────────────────────────────┐
    │  STAGE 2: ORGANIC RANKINE CYCLE (ORC)                    │
    │  Temperature: 300→100°C                                  │
    │  Efficiency: 10-15%                                      │
    │  Working fluid: pentane, ethanol, or silicone oil        │
    │                                                          │
    │  [Evaporator] ←── heat in ←── Stirling cold end          │
    │  [Condenser] ──→ heat out ──→ Stage 3                    │
    │       │                                                  │
    │       v                                                  │
    │  [Scroll Expander or Tesla Turbine] → [Generator]        │
    └──────────────────────────────────────────────────────────┘
                           |
                           | (~100°C heat rejection)
                           v
    ┌──────────────────────────────────────────────────────────┐
    │  STAGE 3: TEG ARRAY + THERMAL USE                        │
    │  Temperature: 100→40°C                                   │
    │  TEG Efficiency: 3-5%                                    │
    │                                                          │
    │  [TEG Hot Side] ←── ORC condenser outlet                 │
    │  [TEG Cold Side] ──→ Coolant Loop ──┬──→ Water Tank       │
    │       │                            │                     │
    │       v                            └──→ Earth Loop       │
    │  DC Output (trickle power for electronics)               │
    │                                                          │
    │  [Water Tank: 40-60°C] ──→ Domestic hot water            │
    │                        ──→ Space heating                 │
    └──────────────────────────────────────────────────────────┘
                           |
                           v
    ┌──────────────────────────────────────────────────────────┐
    │  EARTH COOLING LOOP (Ground Heat Sink)                   │
    │                                                          │
    │  Ground temperature: ~10-15°C (stable year-round)        │
    │  Depth: 1.5-2 m (horizontal trench)                      │
    │                                                          │
    │  Modes:                                                  │
    │  - Water tank needs heat → route through tank first,     │
    │    then earth loop cools remainder                       │
    │  - Tank full/hot → bypass tank, earth loop only          │
    │  - Diverter valve switches between modes                 │
    │                                                          │
    │  Implementation:                                         │
    │  - Horizontal ground loop: copper or PEX tubing          │
    │  - Circulating coolant (water/glycol mix)                │
    │  - Small circulation pump (powered by TEG output)        │
    │  - Loop sized to prevent soil thermal saturation         │
    │                                                          │
    │  Benefits:                                               │
    │  - Lowers TEG cold side from ~40°C to ~15°C             │
    │  - Boosts TEG output (~2x with larger ΔT)               │
    │  - Stable performance regardless of weather/season       │
    └──────────────────────────────────────────────────────────┘
                           |
                           v
                    [Ground Dissipation]
```

---

## Key Design Principles

1. **Cascaded conversion** — each stage operates in its optimal temperature band
2. **Series heat flow** — heat rejected by one stage feeds the next
3. **No wasted heat** — final stage provides domestic hot water/heating
4. **Graceful degradation** — system still works if one stage is offline

---

## Heat Flow Configurations

### Series (Recommended)

- Stirling rejects heat at ~300°C → ORC evaporator inlet
- ORC rejects heat at ~100°C → TEG hot side or water tank
- Single heat extraction point from sand battery
- Simpler plumbing, natural temperature cascade

### Parallel (Alternative)

- Each stage taps the sand battery directly at appropriate temperature zones
- Requires thermal stratification management in storage
- Higher complexity but can run all stages simultaneously at full temperature differential

---

## Efficiency Summary

### Per-Stage

| Stage | Temperature Range | Efficiency |
|-------|-------------------|-----------|
| Solar collection (1 m parabolic dish) | — | ~70% |
| Thermal storage (sand, round-trip) | — | 90–99% |
| **Stage 1:** Stirling engine | 600→300°C | 15–25% |
| **Stage 2:** ORC | 300→100°C | 10–15% |
| **Stage 3:** TEG | 100→40°C | 3–5% |

### Cascade Conversion (100 kWh thermal input)

| Stage | Input | Electrical Output | Heat to Next Stage |
|-------|-------|-------------------|-------------------|
| Stirling (20%) | 100 kWh | 20 kWh | 80 kWh @ 300°C |
| ORC (12%) | 80 kWh | 9.6 kWh | 70.4 kWh @ 100°C |
| TEG (4%) | 70.4 kWh | 2.8 kWh | 67.6 kWh @ 40°C |
| **Total electrical** | — | **32.4 kWh** | — |
| Thermal (hot water) | — | — | **67.6 kWh** |

**Combined heat-to-electric efficiency: ~32%** (vs. ~15% for Stirling alone)

### Overall Solar-to-Electric

| Pathway | Efficiency |
|---------|-----------|
| Solar collection | 60% |
| Thermal storage | 95% |
| Cascade conversion | 32% |
| **Overall solar-to-electric** | **~18%** |

### Total Energy Utilization

| Output | From 100 kWh Solar |
|--------|-------------------|
| Electrical | ~18 kWh |
| Useful thermal (DHW/heating) | ~38 kWh |
| Losses (insulation, ambient) | ~44 kWh |
| **Total utilization** | **~56%** |

With better insulation and larger-scale storage, total utilization can reach **70–80%**.

---

## Sand Battery → Stirling Heat Pipe Interface

### Problem

The optimizer consistently shows a 280–390°C temperature drop between the sand bed (600°C) and the Stirling heater head gas. This external resistance — governed by `h_source_to_heater` — is the single largest efficiency bottleneck in the system and cannot be solved by engine geometry alone. Natural convection from loose sand to a metal surface yields h ≈ 50–250 W/m²K, which at 550 W input produces an unacceptable ΔT.

### Chosen Solution: Sodium Heat Pipes

A bundle of sealed sodium heat pipes runs vertically through the sand battery with hot ends buried in the sand core and cold ends bonded directly to the Stirling heater head exterior. Heat pipes transfer heat via liquid-vapour phase change with effective thermal conductivity of 10,000–100,000 W/mK — hundreds of times better than solid copper. The entire sand-to-gas ΔT drops to approximately 5–20°C.

**How it works:**
1. Sand at 600°C heats the pipe hot end → liquid sodium evaporates (absorbs latent heat)
2. Vapour travels through the hollow core to the cold end with near-zero ΔT
3. Vapour condenses at the heater head → releases latent heat to the engine
4. Liquid wicks back via internal sintered or grooved wick (no pump needed)

**Layout:**
```
        Sand battery silo (500-600°C)
    ┌──────────────────────────────────┐
    │  ║   ║   ║   ║   ║   ║   ║     │  ← heat pipe hot ends (buried 2/3 depth)
    │  ║   ║   ║   ║   ║   ║   ║     │
    └──╫───╫───╫───╫───╫───╫───╫─────┘
       ║   ║   ║   ║   ║   ║   ║        ← insulated adiabatic section
       ╚═══╩═══╩═══╩═══╩═══╩═══╝
                   │
         [bonded manifold block]          ← cold ends brazed to heater head
                   │
         [Stirling heater head]           ← ΔT ≈ 5-20°C sand-to-gas
```

**Key properties:**
- No moving parts, no circulation pump
- Works in any orientation (gravity-assisted preferred: hot end up)
- Lifetime: effectively unlimited once sealed (no consumables)
- Pipe material: steel or Inconel (compatible with sodium at 600°C)
- Wick: sintered stainless steel powder or longitudinal grooves

### Working Fluid Selection

| Fluid | Temp Range | Toxicity | Handling | Notes |
|---|---|---|---|---|
| **Sodium (Na)** | 500–900°C | Low (reactive, not toxic) | Inert atmosphere fill | **Primary choice.** Standard for this range. Used in fast reactors and industrial furnaces. Sealed steel tube is safe indefinitely. Reacts with air/water during fabrication only. |
| **NaK alloy (Na-K)** | 300–800°C | Low (reactive) | Easier than pure Na (liquid at RT) | Liquid at room temperature — easiest to fill and handle. ~78% K by weight for lowest melting point (−12.6°C). Good first-build option. |
| **Potassium (K)** | 400–800°C | Low (reactive) | Inert atmosphere fill | Similar to sodium. Slightly lower melting point (63°C vs 98°C), easier cold-start. Less common commercially. |
| **Cesium (Cs)** | 400–1,000°C | Low (reactive) | Inert atmosphere fill | Best thermodynamic performance of all alkali metals. Liquid at 29°C — easiest cold-start. Very expensive (~$100/g). |
| **Lithium (Li)** | 600–1,200°C | Low (reactive) | Inert atmosphere fill | Excellent for >700°C. Lower end of range (600°C) is marginal. Higher vapour pressure reduces wick requirements. Most demanding to fabricate. |
| **Sulfur (S)** | 450–700°C | **Non-toxic** | Simple (inert gas fill) | Only non-reactive option in this range. No alkali metal handling needed. Corrosive to some metals at high temp — use Inconel pipe. Less studied than alkali metals. Lower latent heat. |
| **Bismuth (Bi)** | 500–1,100°C | Mildly toxic | Complex (high melt point 271°C) | Dense liquid, low vapour pressure, difficult wick design. Rarely used. |
| **Naphthalene** | 150–450°C | Low | Simple | Upper limit ~450°C — marginally useful at our 500°C+ temperatures. Better for ORC-range applications. |
| **Dowtherm A** | 150–400°C | Low | Simple | Below our temperature range. Useful for ORC stage heat pipe applications. |
| **Mercury (Hg)** | 200–650°C | **Highly toxic** | Hazardous | Excluded — violates non-toxic materials constraint. |
| **Lead (Pb)** | 600–1,100°C | **Toxic** | Hazardous | Excluded — violates non-toxic materials constraint. |

### Recommendation

**Primary: Sodium** — best-documented, commercially available, 500–900°C range is ideal. Pre-made sodium heat pipes are available from industrial furnace suppliers.

**Alternative for first build: NaK alloy** — liquid at room temperature makes it significantly easier to fill and seal without a heated glove box. Slightly lower max temperature but sufficient for 600°C operation.

**Sulfur** if alkali metal handling is impractical — non-toxic, no special atmosphere needed, but requires more development work and Inconel containment.

### Effect on Optimizer

`h_source_to_heater` will be added as a design variable when the sand battery interface section is designed. With heat pipes, effective h rises to ~5,000–20,000 W/m²K, reducing external ΔT from ~300°C to ~5–20°C and recovering an estimated 20–30 W of additional electrical output.

---

## Earth Cooling Loop

### Rationale

The TEG stage benefits most from a low, stable cold-side temperature. Ambient air fluctuates significantly (0-40°C+ depending on season and climate), while ground temperature at 1.5-2 m depth remains roughly **10-15°C year-round** in most temperate/arid climates.

Lowering the TEG cold side from ~40°C to ~15°C nearly doubles the temperature differential across the TEG, boosting its output.

### Carnot Impact on TEG Stage

| Cold sink | T_cold (K) | Carnot η (from 100°C) | TEG @ 40% Carnot |
|-----------|-----------|----------------------|-------------------|
| Air (35°C, summer) | 308 | 17.4% | 7.0% |
| Water tank (40°C) | 313 | 16.1% | 6.4% |
| Ground (13°C) | 286 | 23.3% | 9.3% |

### Dual-Use Design

The coolant loop from the TEG cold side serves two functions:

1. **Domestic hot water pre-heating** — When the water tank needs heat, coolant flows through a heat exchanger in the tank first, pre-heating water to 40-60°C
2. **Earth cooling** — Coolant then continues to (or bypasses to) the buried ground loop, which dissipates remaining heat to achieve the lowest possible TEG cold-side temperature

A diverter valve switches between modes:
- **Tank needs heat:** TEG → water tank → earth loop
- **Tank satisfied:** TEG → earth loop (bypass tank)

### Ground Loop Sizing

- **Type:** Horizontal slinky or straight runs at 1.5-2 m depth
- **Material:** PEX tubing (cheaper) or copper (better conductivity)
- **Coolant:** Water/propylene glycol mix (non-toxic, freeze-protected)
- **Circulation:** Small DC pump powered by TEG output
- **Length:** Must be sized to avoid thermal saturation of surrounding soil — longer loops with wider spacing dissipate heat more effectively
- **Soil conductivity:** Sandy/moist soil conducts heat ~2x better than dry clay; site-specific testing recommended
