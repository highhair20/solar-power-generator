# Parabolic Dish Collector Design

## Overview

This document details the design of the primary solar collector: a 1 m parabolic dish targeting **~140 W electrical output** in the US Southwest.

---

## Sizing Calculations

### Power Budget

Starting from a 1 m dish aperture:

| Parameter | Value | Derivation |
|-----------|-------|------------|
| **Design diameter** | **1.0 m** | Design requirement |
| **Aperture area** | **0.785 m²** | pi/4 x 1.0² |
| Peak DNI (US Southwest) | 1000 W/m² | Clear-sky noon, summer |
| Peak solar input | 785 W | 0.785 m² x 1000 W/m² |
| Overall solar-to-electric efficiency | ~18% | Collection x storage x conversion |
| **Peak electrical output** | **~140 W** | 785 W x 0.18 |

### Location Assumptions

| Parameter | Value |
|-----------|-------|
| Location | US Southwest (Arizona, Nevada, New Mexico) |
| Annual DNI | ~2500 kWh/m²/year |
| Daily DNI | 7-8 kWh/m²/day (annual average) |
| Peak DNI | ~1000 W/m² |
| Design ambient temperature | 35°C (summer peak) |

---

## Dish Geometry

### Key Dimensions

| Parameter | Value | Notes |
|-----------|-------|-------|
| Aperture diameter | 1.0 m | Circular paraboloid |
| Aperture area | 0.785 m² | pi/4 x D² |
| Rim angle | 45° | Balance of concentration ratio and fabrication ease |
| Focal length | 0.60 m | f = D / (4 x tan(rim_angle/2)) |
| f/D ratio | 0.60 | Moderate — good flux uniformity on receiver |
| Dish depth | 0.10 m | D² / (16f) |
| Surface area | ~0.88 m² | Reflective surface (slightly larger than aperture) |

### Rim Angle Selection

A **45° rim angle** was chosen as a compromise:
- **Steeper (55-60°):** Higher concentration ratio, but deeper dish, harder to fabricate, more wind loading
- **Shallower (30-35°):** Easier to build, but lower concentration, larger focal spot
- **45°:** Achievable concentration ratio of ~1000 suns (with good optics), moderate depth (0.10 m), proven in practice

### Concentration Ratio

| Parameter | Value |
|-----------|-------|
| Geometric concentration ratio | ~1000x (theoretical) |
| Practical concentration ratio | 500-800x |
| Receiver aperture diameter | ~4 cm |
| Peak flux at receiver | 500-800 kW/m² |

---

## Mirror Surface

### Segmentation

The dish is divided into **8 petals** (gore segments), each a near-triangular section of the paraboloid:
- Petal width at rim: ~0.39 m (pi x 1.0 / 8)
- Petal length (center to rim): ~0.53 m
- Individual petal area: ~0.098 m²

Eight segments balance:
- Manageable petal size for fabrication
- Sufficient approximation of the paraboloid surface
- Practical number of seams/gaps (losses < 2%)

### Mirror Material

**Alanod MIRO-SUN weatherproof** (anodized aluminum reflector sheet):
- Solar-weighted reflectance: ≥ 90%
- Weatherproof coating for outdoor durability
- Formable onto curved substrates
- Non-toxic, recyclable aluminum
- Available in rolls (0.4-0.5 mm thickness)

Each petal: MIRO-SUN sheet bonded to a shaped substrate (sheet metal or fiberglass rib-and-skin).

### Substrate Options

| Option | Pros | Cons |
|--------|------|------|
| Sheet steel (pressed) | Durable, weldable to frame | Heavy, requires press tooling |
| Fiberglass on foam mold | Lightweight, DIY-friendly | Less durable, more labor |
| Aluminum sheet (hydroformed) | Lightweight, corrosion resistant | Requires hydroforming setup |

**Recommended:** Sheet steel ribs with fiberglass skin for initial prototype — combines structural rigidity with achievable surface accuracy.

---

## Receiver

### Type: Cavity Receiver

A cavity receiver is selected over an external receiver for higher efficiency at the target temperatures (500-700°C):

| Parameter | Value |
|-----------|-------|
| Type | Cylindrical cavity |
| Cavity aperture diameter | 4 cm |
| Cavity depth | ~6 cm (1.5x aperture diameter) |
| Cavity inner diameter | ~7 cm |
| Absorber material | Black-painted steel or Inconel |
| Insulation | Ceramic fiber blanket (outer surface) |
| Position | Focal point, 0.60 m from dish vertex |

### Receiver Performance

| Parameter | Value |
|-----------|-------|
| Absorptivity of cavity | ≥ 0.95 (effective, due to cavity effect) |
| Radiation losses | ~10% at 600°C |
| Convection losses | ~5% (reduced by cavity geometry) |
| Conduction losses | ~2% (with ceramic fiber insulation) |
| **Receiver thermal efficiency** | **~83%** |

### Heat Transfer

Heat is extracted from the receiver via:
- **Primary:** Forced air circulation through the cavity, directed to the sand battery
- **Alternative:** Thermal oil loop (for lower-temperature operation or longer pipe runs)

Air outlet temperature target: 550-650°C

---

## Tracking System

### Mount Type: Altitude-Azimuth (Alt-Az)

| Parameter | Specification |
|-----------|--------------|
| Mount type | Alt-azimuth (two-axis) |
| Azimuth range | 0-360° (continuous or ±180°) |
| Elevation range | 0-90° |
| Tracking accuracy | ≤ 0.1° (required for concentration ratio > 500) |
| Drive type | Worm gear + DC motor (each axis) |
| Motor size | ~5-10 W per axis (intermittent duty) |

### Solar Position Algorithm

- Use NREL Solar Position Algorithm (SPA) — accuracy ±0.0003°
- Inputs: latitude, longitude, date/time, atmospheric pressure, temperature
- Open-source implementations available (C, Python)
- Feedback: optional sun sensor (quadrant photodiode) for closed-loop correction

### Tracking Power Budget

| Component | Power |
|-----------|-------|
| Controller (microcontroller) | ~1 W |
| Azimuth motor (intermittent) | ~2 W average |
| Elevation motor (intermittent) | ~2 W average |
| Sun sensor (if used) | < 1 W |
| **Total tracking power** | **~6 W** |

Tracking consumes ~4% of electrical output — acceptable.

---

## Support Structure

### Frame Design

- **Material:** Mild steel tube (square or round section)
- **Main members:** 25-30 mm square tube, 1.5-2 mm wall
- **Configuration:** Central pedestal with rotating yoke
- **Dish backup structure:** Radial ribs from central hub to rim ring
- **Foundation:** Concrete pad or ground screws

### Wind Loading

| Condition | Action |
|-----------|--------|
| Operating (< 40 km/h) | Normal tracking |
| High wind (40-60 km/h) | Stow at zenith (face up, minimum profile) |
| Storm (> 60 km/h) | Stow face-down or at zenith with locks engaged |

Design wind load (operating): ~55 N lateral force on dish at 40 km/h.

### Weight Estimate

| Component | Weight |
|-----------|--------|
| Mirror petals (8x) | ~3 kg |
| Dish backup structure | ~5 kg |
| Receiver + support arm | ~3 kg |
| Tracking drives + mount | ~8 kg |
| Pedestal + base | ~15 kg |
| **Total** | **~34 kg** |

---

## Expected Performance

### Optical

| Parameter | Value |
|-----------|-------|
| Mirror reflectance | 90% (MIRO-SUN) |
| Intercept factor | 95% (fraction of reflected light hitting receiver) |
| Blocking/shadowing | 2% loss (receiver shadow + support arms) |
| **Optical efficiency** | **~84%** |

### Thermal (Receiver)

| Parameter | Value |
|-----------|-------|
| Receiver absorptance (cavity) | 95% |
| Radiation loss | 10% |
| Convection + conduction loss | 7% |
| **Receiver thermal efficiency** | **~83%** |

### Overall Collector

| Parameter | Value |
|-----------|-------|
| Peak solar input | 785 W (at 1000 W/m²) |
| After optical losses | 659 W (84% optical efficiency) |
| After receiver losses | 547 W (83% receiver efficiency) |
| **Peak thermal output to storage** | **~550 W** |
| **Overall collector efficiency** | **~70%** |

### Daily Energy Collection

| Season | Daily DNI | Solar Hours | Daily Thermal Output |
|--------|-----------|-------------|---------------------|
| Summer | 8 kWh/m²/day | ~10 h | ~4.4 kWh |
| Equinox | 6.5 kWh/m²/day | ~8 h | ~3.6 kWh |
| Winter | 5 kWh/m²/day | ~6 h | ~2.7 kWh |
| **Annual average** | **~7 kWh/m²/day** | **~8 h** | **~3.8 kWh/day** |

---

## Open Questions

- [ ] Exact petal forming process — press brake vs. English wheel vs. fiberglass mold
- [ ] Receiver absorber coating — high-temperature solar selective coating vs. black paint
- [ ] Heat transfer fluid — air vs. thermal oil trade study
- [ ] Wind stow mechanism — manual vs. automatic
- [ ] Foundation type for specific site conditions
