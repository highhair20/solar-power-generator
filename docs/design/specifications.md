# System Specifications

## Overview

This document captures target specifications for the solar power generator system. Values will be refined as design progresses.

---

## Target Performance

| Parameter | Target | Notes |
|-----------|--------|-------|
| Solar collection efficiency | 55–70% | Scheffler or parabolic dish |
| Peak storage temperature | 500–600°C | Sand battery |
| Storage capacity | TBD | Depends on sizing |
| Heat-to-electric efficiency | ~32% | Cascade (Stirling + ORC + TEG) |
| Overall solar-to-electric | ~18% | Collection × storage × conversion |
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

## Size Targets (TBD)

| Parameter | Small Scale | Medium Scale |
|-----------|-------------|--------------|
| Collector area | 2–5 m² | 10–25 m² |
| Storage volume | 0.5–1 m³ | 2–5 m³ |
| Storage capacity | 25–60 kWh | 100–300 kWh |
| Peak electrical output | 100–500 W | 1–5 kW |
| Daily electrical yield | 0.5–2 kWh | 5–20 kWh |

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

- [ ] Exact collector dimensions
- [ ] Storage silo dimensions and insulation thickness
- [ ] Stirling engine swept volumes and configuration
- [ ] ORC working fluid selection
- [ ] TEG array size
- [ ] Electrical system voltage and configuration
