# Thermal Storage Research

## Overview

This document covers research into thermal energy storage methods for the solar power generator project.

---

## Primary: Sand Battery (High Temperature Sensible Heat)

- Sand heated to **500–600°C** in an insulated steel silo
- Inspired by the Finnish Polar Night Energy installation (operational 2022)
- Energy density: ~50–60 kWh/m³
- Storage duration: days to months (< 1°C/day loss in large systems)
- Materials: silica sand, steel container, firebrick + mineral wool insulation, nichrome heating elements
- **Zero toxicity**, sand is free and indestructible, no degradation over time
- Round-trip efficiency: ~90–99% thermal, ~30–50% electrical (limited by heat engine)

### Finnish Sand Battery (Polar Night Energy) Reference

- First installed in Kankaanpää, Finland (2022)
- ~100 tonnes of sand in steel silo (~4m diameter, ~7m tall)
- Capacity: ~8 MWh thermal
- Operating temperature: up to 500–600°C
- Heating method: resistive electric elements
- Discharge: hot air circulated through sand to heat exchangers
- Heat loss: <1°C per day in large installations

---

## Alternative: Rock/Gravel Bed

- Similar benefits to sand; quartzite/basalt handles 700°C+
- Slightly better airflow through larger particles
- Even simpler construction

---

## Secondary Buffer: Erythritol Phase Change Material (PCM)

- Food-grade sugar alcohol, melting point **118°C**, latent heat **340 kJ/kg**
- Energy density: ~80–120 kWh/m³ (highest of non-toxic organic PCMs)
- Useful as a thermal buffer between high-temp storage and heat engine
- Provides stable input temperature during phase transition
- Bio-derived, completely non-toxic

### Other Non-Toxic PCM Options

| Material | Melting Point | Latent Heat | Notes |
|----------|---------------|-------------|-------|
| Erythritol | 118°C | 340 kJ/kg | Best for this application |
| Paraffin wax | 20–70°C | 150–250 kJ/kg | Too low temp, flammable |
| Fatty acids | 45–70°C | 150–210 kJ/kg | Bio-derived, low temp |
| Salt hydrates | 15–120°C | 150–250 kJ/kg | Phase separation issues |

---

## Future Scaling Option: Falling Particle Receiver (Direct Sand/Gravel Heating)

- Sand or gravel particles fall directly through the concentrated focal spot, absorbing heat without an intermediate transfer fluid
- Eliminates the heat exchanger between transfer fluid and storage — the storage medium *is* the transfer medium
- Sand/gravel handles 1000°C+ with no degradation
- No pumps, no pressure vessels, no toxic fluids
- Active research area: Sandia National Labs falling particle receiver program

### Why Not for Iteration One

- Our focal spot is only ~4 cm (1 m dish) — difficult to get meaningful particle flow through such a small region
- Requires a mechanical lift system (bucket elevator, auger) to cycle particles from cool storage back up to the receiver
- Particle flow rate control is tricky — too fast and grains don't heat sufficiently, too slow and they overheat or clog
- Dust and abrasion on moving parts
- The receiver sits 0.60 m above the dish vertex, adding complexity for particle transport

### When It Makes Sense

- Larger dish sizes (3+ m) with larger focal spots
- Higher thermal power (multiple kW) where the fluid-to-storage heat exchanger becomes a significant cost and efficiency bottleneck
- Systems where eliminating the heat transfer fluid simplifies the overall design

---

## Sand Battery Discharge: Heat Pipe Interface

Direct extraction of heat from the sand battery to the Stirling engine heater head is the primary design challenge. Natural convection from loose sand gives only h ≈ 50–250 W/m²K, producing a ~300–390°C temperature drop that dominates the system loss budget.

**Chosen approach: sodium heat pipes** embedded in the sand core with cold ends bonded to the Stirling heater head. Effective thermal conductivity 10,000–100,000 W/mK; reduces sand-to-gas ΔT to ~5–20°C with no moving parts.

See [System Architecture — Sand Battery → Stirling Heat Pipe Interface](../design/system-architecture.md) for full working fluid table, layout diagram, and design rationale.

---

## Waste Heat Recovery: Water Tank

- Captures low-grade waste heat from engine exhaust
- Useful for domestic hot water / space heating
- Simplest and cheapest storage method

---

## Comparison Table

| Storage Type | Energy Density | Temp Range | Duration | Toxicity | DIY Score |
|--------------|---------------|------------|----------|----------|-----------|
| Sand battery | 50–60 kWh/m³ | 20–600°C | Days–months | None | 4/5 |
| Rock/gravel | 30–40 kWh/m³ | 20–750°C | Days | None | 5/5 |
| Erythritol PCM | 80–120 kWh/m³ | 118°C | Hours–days | None | 4/5 |
| Water tank | 60–80 kWh/m³ | 20–95°C | Hours–days | None | 5/5 |
