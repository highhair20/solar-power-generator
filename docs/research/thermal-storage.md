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
