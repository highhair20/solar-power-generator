# Solar Power Generator

A solar thermal power generator — it converts sunlight to heat, stores it, then converts heat to electricity on demand.

## How It Works

**Collection:** A 1m parabolic dish concentrates sunlight onto a cavity receiver, heating a working fluid to 500-600°C.

**Storage:** The heat goes into a thermal battery (inspired by Polar Night Energy), allowing electricity generation even when the sun isn't shining.

**Conversion:** A three-stage cascade extracts electricity at different temperature ranges:

1. **Stirling engine** (600→300°C, 15-25% efficiency) — the primary converter, using a free-piston design with pressurized helium
2. **Organic Rankine Cycle** (300→100°C, 10-15%) — captures mid-grade heat
3. **Thermoelectric generators** (100→40°C, 3-5%) — scavenges remaining low-grade heat

Leftover heat (~40°C) provides hot water/space heating, pushing total energy utilization to 60-80%.

## Current State

The project is in **research & design** phase:

- **Docs** in `docs/` cover research on each subsystem and design specs
- **CAD models** in `cad/` include parametric CadQuery scripts for the parabolic dish, cavity receiver, and two Stirling engine designs (gamma-type and free-piston)
- **Analysis code** in `cad/stirling/` for thermodynamic modeling and optimization

## Design Constraints

- **No toxic or exotic materials** — everything commonly available, unlike PV panels that use lead/cadmium
- **Green to build** — minimal environmental impact in manufacturing
- **Maximum efficiency** — there is no specific target. The goal is to design a system that is more efficient than any PV or other solar collecting technology that currently exists.

A 24" Edmund Optics dish serves as the prototype test platform before scaling to the full 1m dish.

## Stirling Engine Optimizer

The optimizer (`cad/stirling/optimize.py`) uses a computational engineering loop to search for optimal Stirling engine geometries:

```
Design variables → analysis.evaluate() → Score/constraints → NSGA-II → Better designs
```

### Physics Model (`cad/stirling/analysis.py`)

A first-principles thermodynamic model that computes performance from 7 loss mechanisms rather than a simple "fraction of Carnot" estimate:

1. **Pumping loss** — pressure drop through heat exchangers (Kays & London correlations)
2. **Shuttle heat loss** — displacer thermal shuttling (Urieli & Berchowitz)
3. **Displacer/vessel wall conduction** — axial heat leak through the shell
4. **Regenerator enthalpy loss** — imperfect heat recovery (1 - effectiveness)
5. **Gas spring hysteresis** — irreversible compression in the bounce space
6. **Seal leakage** — pressure-volume work lost through clearance gaps

Uses the **Schmidt cycle** (isothermal, sinusoidal motion) as the ideal baseline, then subtracts each loss to get net electrical output.

### Optimization (`cad/stirling/optimize.py`)

Uses **pymoo's NSGA-II** (multi-objective genetic algorithm) with:

**22 design variables** — geometry parameters like piston/displacer stroke, frequency, charge pressure, cooler tube count/diameter, regenerator length/porosity, clearances, phase angle, etc.

**2 objectives** (Pareto front):
1. Maximize electrical power
2. Minimize dead volume ratio

**7 constraints** that must all be satisfied:
- Regenerator effectiveness > 90%
- Total HX pressure drop < 5% of mean pressure
- Heater gas temperature drop < 80°C
- Piston and displacer seal leakage < 5% each
- Natural frequency > 10 Hz
- Electrical output >= 60 W

Default run: **120 population × 100 generations** (~12,000 design evaluations). Uses Latin Hypercube Sampling for the initial population, SBX crossover, and polynomial mutation.

The output includes a summary table of top Pareto-front designs and can generate CAD parameter updates (`--cad` flag) to directly update the 3D model with optimized dimensions.

```bash
python optimize.py              # run optimization
python optimize.py --gens 200   # more generations
python optimize.py --pop 200    # larger population
python optimize.py --report     # detailed report for best design
python optimize.py --cad        # print CAD parameter update block
```

## Project Structure

```
├── docs/
│   ├── research/      # Research notes and findings
│   ├── design/        # System design documentation
│   └── computational/ # Simulation and optimization workflows
├── cad/
│   ├── collector/     # CadQuery scripts for dish & receiver
│   │   └── output/    # Generated STEP/STL/DXF
│   └── stirling/      # CadQuery scripts + analysis/optimizer
│       └── output/    # Generated STEP/STL
├── src/               # (Future) Simulation code
├── simulations/       # (Future) CFD/FEA cases
└── fabrication/       # (Future) Manufacturing outputs
```

## License

This project is dual-licensed:

- **Hardware, CAD, and documentation** — [CERN-OHL-S-2.0](LICENSE-CERN-OHL-S-2.0.txt)
- **Software and simulation code** — [GPL-3.0](LICENSE-GPL-3.0.txt)
