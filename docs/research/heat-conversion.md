# Heat-to-Electricity Conversion Research

## Overview

This document covers research into methods for converting stored thermal energy into electricity. The project uses a **hybrid cascade approach** with multiple conversion stages optimized for different temperature ranges.

---

## Hybrid Cascade Rationale

A single heat engine cannot efficiently extract energy across the full temperature range as the sand battery cools from 600°C to ambient. A **cascaded multi-stage approach** uses different conversion technologies optimized for different temperature bands, extracting **30–50% more electricity** from the same stored heat compared to a single engine.

### Cascade Efficiency Comparison

| Temperature Range | Single Stirling | Hybrid Cascade |
|-------------------|-----------------|----------------|
| 600→300°C | 20% eff | 20% (Stirling) |
| 300→100°C | ~8% (poor) | 12% (ORC optimized) |
| 100→40°C | ~0% (can't operate) | 4% (TEG) or thermal |
| **Effective overall** | **~12–15%** | **~18–25%** |

---

## Stage 1: High Temperature (600→300°C) — Stirling Engine

- External combustion, closed-cycle heat engine
- Efficiency: **15–25%** in this temperature range
- Optimal operating band matches the sand battery's high-temperature phase
- Materials: stainless steel, copper, aluminum, graphite seals, air or helium working gas
- **All materials non-toxic**, no exotic components
- Highly DIY-feasible (one of the most popular DIY heat engine projects)
- Quiet, long lifespan (50,000+ hours), low maintenance
- Configuration: **Gamma-type** recommended for easier heat input from storage; air-charged for simpler sealing, helium for higher performance
- Free-piston variant uses **magnetic springs** (opposing SmCo ring magnets) instead of mechanical flexure springs — eliminates fatigue failure, the #1 life-limiting component. SmCo (samarium cobalt) chosen over NdFeB for high-temperature operation near the displacer (rated to 300°C vs NdFeB's 150°C limit).
- Heat rejection at ~250–300°C feeds Stage 2
- DIY cost: $500–$3,000 for a 100 W – 1 kW system

### Stirling Engine Configurations

| Type | Description | DIY Feasibility | Best For |
|------|-------------|-----------------|----------|
| Alpha | Two separate cylinders | Moderate | Higher power |
| Beta | Single cylinder, displacer + power piston | Moderate | Compact design |
| Gamma | Separate cylinders, shared gas space | High | External heat input |

### Free-Piston Stirling Design (Target Architecture)

A sealed pressure vessel filled with pressurized helium. No crankshaft, no sliding seals, no connecting rod. Every internal part floats freely.

#### Components (bottom to top)

1. **Vessel floor** — sealed bottom of the pressure vessel
2. **Centering magnet** — magnet ring on the floor that repels the piston's magnet ring, keeping the piston suspended at rest so the bounce space always has volume for startup
3. **Bounce space** — gas volume between the floor and piston, acts as a gas spring
4. **Power piston** — heavy free-floating cylinder (89mm OD, 0.5mm radial clearance seal in 90mm bore) with a permanent magnet ring recessed concentrically around it
5. **Alternator stator** — 55mm coil housing wrapped around the *outside* of the vessel, aligned with the piston's magnet ring (sized for 10-15mm stroke)
6. **External cooler fins** — annular fins on the vessel for heat rejection, aligned with internal cooler
7. **Internal cooler** — full-bore tube bundle (48 tubes × 3mm dia) spanning the entire bore cross-section. No center bypass — gas must flow through tubes for heat transfer to the vessel wall.
8. **Regenerator** — full-bore packed wire mesh housing (45mm long, 80-mesh SS316 stacked screens, ~70% porosity). Fills entire bore. Recovers 90-95% of heat between hot and cold spaces.
9. **Magnetic spring, fixed ring** — SmCo magnet ring mounted to the vessel inner wall
10. **Magnetic spring, moving ring** — SmCo magnet ring bonded to the outer edge of the displacer's bottom face, repels the fixed ring below (20mm nominal gap for 10-15mm stroke)
11. **Displacer** — lightweight hollow cylinder that shuttles gas between hot and cold zones, centered by clearance seal (0.75mm radial gap, no rod)
12. **Hot space** — 12mm gas volume above the displacer (minimized dead volume)
13. **Heater head** — finned cap that inserts into the vessel top, absorbs concentrated solar heat. 12 internal radial fins increase gas-side heat transfer area 3-5x.

#### Operating Cycle (~50-60 Hz)

1. **Displacer drops** → gas flows up into the hot space near the heater head → heats up → pressure rises
2. **High pressure pushes piston down** → compresses bounce space gas → magnet ring sweeps past stator coils → electricity generated
3. **Displacer rises** → wall-mounted magnetic spring rings push it back up → gas displaced down past cooler fins → gas cools → pressure drops
4. **Bounce space pushes piston back up** → compressed gas spring expands → magnet ring sweeps past stator again → more electricity

#### Key Design Choices

- **No rod** — displacer floats freely, centered by 2mm clearance gap to bore. Magnetic spring ring on its outer edge provides restoring force.
- **Wall-mounted magnetic springs (SmCo)** — both fixed and moving rings hug the vessel wall and displacer edge. SmCo magnets rated to 300°C for reliable operation near the hot displacer. 20mm nominal gap allows full 10-15mm displacer stroke.
- **No mechanical springs** — magnetic repulsion replaces flexure springs. No fatigue failure, no wear, indefinite life.
- **No sliding seals** — both piston (0.5mm gap) and displacer (0.75mm gap) use clearance seals. At 50-60 Hz, gas doesn't have time to leak through the tiny gaps.
- **Full-bore heat exchangers** — cooler tube bundle and regenerator mesh fill the entire bore cross-section. No center bypass path — all gas is forced through the heat exchangers.
- **Minimized dead volume** — 12mm hot space, 3mm piston-to-cooler gap, full-bore HXs. Dead volume ratio ~0.7:1 (target < 1.0:1).
- **Internal heater fins** — 12 radial fins inside the heater head increase gas-side heat transfer area 3-5x, reducing gas temperature drop from ~109°C to ~25-35°C.
- **Centering magnet** — repels the existing alternator magnet ring on the piston to hold it at rest position.
- **Fully sealed** — pressurized helium stays inside permanently. Only AC electricity exits through stator wires.

---

## Stage 2: Medium Temperature (300→100°C) — Organic Rankine Cycle (ORC)

- Uses low-boiling-point organic fluid optimized for this temperature range
- Efficiency: **10–15%** at 150–300°C
- Working fluids (non-toxic, low GWP):
  - **Pentane/isopentane**: boiling point 28–36°C, good for 100–200°C
  - **Ethanol**: boiling point 78°C, good for 120–250°C, green/bio-derived
  - **Silicone oil (MM/MDM)**: for higher end of range (200–350°C), very stable
- Heat rejection at ~80–100°C feeds Stage 3 or thermal use
- More complex than Stirling but excels where Stirling efficiency drops off

### Expander Options for ORC

| Expander Type | Efficiency | DIY Feasibility | Notes |
|---------------|------------|-----------------|-------|
| **Scroll expander** | 60–90% isentropic | Moderate | Modified HVAC scroll compressor run in reverse; proven, predictable |
| **Tesla turbine** | 30–60% | High | Bladeless disc turbine; extremely simple to fabricate; works best at low pressure ratios |
| Screw expander | 50–70% | Low | Requires precision machining |
| Piston expander | 60–80% | Moderate | More complex, higher maintenance |

### Tesla Turbine as ORC Expander

Nikola Tesla's bladeless turbine (patented 1913) uses stacked smooth discs instead of blades. Fluid enters at the disc edges, transfers momentum via boundary layer viscous drag, and exits through central holes. Recent research confirms viability for small-scale ORC:

- **Efficiency**: 30–60% depending on design optimization (research has achieved 64% with N-hexane)
- **Advantages over scroll expander**:
  - Far simpler to fabricate — flat discs with holes, no precision curves
  - Handles two-phase flow and contaminated fluids without damage
  - Safe failure mode — discs implode rather than throw shrapnel
  - Lower cost — potentially 10x cheaper than scroll
  - Scales down effectively — more competitive at small scale
- **Disadvantages**:
  - Lower peak efficiency than well-designed scroll
  - Optimal at low pressure ratios (may require ORC cycle redesign)
  - High RPM output (10,000–60,000) requires gearing or high-speed generator
  - Narrow optimal operating window
- **Materials**: stainless steel or aluminum discs, standard bearings — all non-toxic
- **DIY approach**: Stack of laser-cut or waterjet-cut discs on a shaft, housed in a simple volute casing
- **Best suited when**: fabrication simplicity is prioritized over peak efficiency, or budget is constrained

---

## Stage 3: Low Temperature (100→40°C) — TEG Array or Direct Thermal Use

### Option A: Thermoelectric Generators (TEG)

- Solid-state, no moving parts, zero maintenance
- Efficiency: **3–5%** at ΔT of 60–80°C
- Always-on trickle power for monitoring electronics, battery maintenance
- Commercial Bi2Te3 modules are $5–20 each
- Provides power even when main engines are off

### Option B: Direct Thermal Use

- Domestic hot water heating
- Space heating
- No conversion losses — 90%+ thermal efficiency
- Often more valuable than the ~4% electrical conversion

---

## Heat Flow Configuration

### Series (Recommended for Simplicity)

- Stirling rejects heat at ~300°C → ORC evaporator inlet
- ORC rejects heat at ~100°C → TEG hot side or water tank
- Single heat extraction point from sand battery
- Simpler plumbing, natural temperature cascade

### Parallel (Higher Peak Power)

- Each stage taps the sand battery directly at appropriate temperature zones
- Requires thermal stratification management in storage
- Higher complexity but can run all stages simultaneously at full temperature differential

---

## Other Conversion Technologies Considered

### Thermoacoustic Engine

- Temperature gradient creates acoustic oscillations driving a linear alternator
- 15–25% efficiency demonstrated
- No sliding seals (main Stirling weakness)
- See exploratory concepts for more detail

### Thermophotovoltaic (TPV)

- Requires 1000°C+ temperatures
- 40%+ efficiency possible with advanced cells
- Current cells use exotic materials (InGaAs, GaSb)
- See exploratory concepts for silicon-based approach

### Thermo-Magnetic Motor (Tesla Patent 396,121)

- Uses Curie point transition to generate motion
- Requires gadolinium (rare earth) for useful temperatures
- <1% practical efficiency with common materials
- Not recommended for this project
