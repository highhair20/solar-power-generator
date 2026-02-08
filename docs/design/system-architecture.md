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
                           | (hot air/fluid extraction)
                           v
    ┌──────────────────────────────────────────────────────────┐
    │  STAGE 1: STIRLING ENGINE                                │
    │  Temperature: 600→300°C                                  │
    │  Efficiency: 15-25%                                      │
    │  Config: Gamma-type, air or helium working gas           │
    │                                                          │
    │  [Hot End] ←── heat in ←── Sand Battery                  │
    │  [Cold End] ──→ heat out ──→ Stage 2                     │
    │       │                                                  │
    │       v                                                  │
    │  [Generator] ──→ AC/DC Output                            │
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
    │  [TEG Cold Side] ──→ Water Tank (DHW/heating)            │
    │       │                                                  │
    │       v                                                  │
    │  DC Output (trickle power for electronics)               │
    │                                                          │
    │  [Water Tank: 40-60°C] ──→ Domestic hot water            │
    │                        ──→ Space heating                 │
    └──────────────────────────────────────────────────────────┘
                           |
                           v
                    [Ambient / Ground]
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
