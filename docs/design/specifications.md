# System Specifications

## Overview

This document captures target specifications for the solar power generator system. Values will be refined as design progresses.

---

## Design Targets

| Parameter | Value |
|-----------|-------|
| **Electrical output (peak)** | **~140 W** |
| **Location** | **US Southwest (~1000 W/m² peak DNI)** |
| **Collector** | **1 m parabolic dish (~0.785 m² aperture)** |

## Target Performance

| Parameter | Target | Notes |
|-----------|--------|-------|
| Solar collection efficiency | ~70% | 1 m parabolic dish (optical 84% x receiver 83%) |
| Peak solar input | 785 W | At 1000 W/m² DNI |
| Peak thermal output to storage | ~550 W | After collector losses |
| Peak storage temperature | 500–600°C | Sand battery |
| Storage capacity | TBD | Depends on autonomy requirement |
| Heat-to-electric efficiency | ~32% | Cascade (Stirling + ORC + TEG) |
| Overall solar-to-electric | ~18% | Collection x storage x conversion |
| Total energy utilization | 60–80% | Including thermal use |

---

## Temperature Ranges

| Stage | Hot Side | Cold Side |
|-------|----------|-----------|
| Solar receiver | 500–700°C | — |
| Sand battery (charged) | 500–600°C | — |
| Sand battery (discharged) | 100–200°C | — |
| Stirling engine | 600°C | 300°C |
| ORC system | 300°C | 100°C |
| TEG array | 100°C | 40°C |
| Hot water output | 40–60°C | — |

---

## System Sizing (140 W Design)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Collector diameter | 1.0 m | Parabolic dish |
| Collector aperture area | 0.785 m² | pi/4 x 1² |
| Collector focal length | 0.60 m | 45° rim angle |
| Peak thermal to storage | ~550 W | 70% collector efficiency |
| Storage volume | TBD | Depends on autonomy requirement |
| Storage capacity | TBD | Depends on autonomy requirement |
| Peak electrical output | ~140 W | Cascade conversion |
| Daily electrical yield | ~1 kWh | Annual average, US Southwest |
| Daily thermal yield | ~3.8 kWh | To storage (annual average) |

---

## Constraints

### Hard Constraints

- No toxic materials
- No exotic materials (rare earth elements limited to TEG modules)
- DIY-buildable with workshop tools
- Safe to operate without special training

### Soft Constraints (Targets)

- Minimize cost
- Maximize efficiency
- Minimize maintenance
- Modular/expandable design

---

## Interface Specifications

### Collector → Storage

- Heat transfer medium: air (baseline) or thermal oil
- Temperature: 500–700°C
- Connection: insulated ducting or piping

### Storage → Stage 1 (Stirling)

- Heat transfer: air circulation or direct contact heat exchanger
- Temperature: 600°C input, 300°C output
- Flow: natural convection or low-power fan

### Stage 1 → Stage 2 (ORC)

- Heat transfer: Stirling cold-end heat exchanger to ORC evaporator
- Temperature: ~300°C
- Medium: ORC working fluid (pentane, ethanol, or silicone oil)

### Stage 2 → Stage 3 (TEG/Thermal)

- Heat transfer: ORC condenser to TEG hot side / water tank
- Temperature: ~100°C
- Medium: water or direct contact

### Electrical Output

- Stirling generator: AC or DC (design dependent)
- ORC generator: AC or DC (design dependent)
- TEG array: DC (low voltage, needs boost converter)
- Combined output: TBD (battery charging, inverter, grid-tie)

---

## Open Specifications

The following parameters require further analysis or optimization:

- [x] Collector dimensions — 1 m diameter parabolic dish (see [Collector Design](collector-design.md))
- [ ] Storage silo dimensions and insulation thickness
- [ ] Stirling engine swept volumes and configuration
- [ ] ORC working fluid selection
- [ ] TEG array size
- [ ] Electrical system voltage and configuration
