# Solar Power Generator

A solar thermal power system with heat storage for on-demand electricity generation.

## Project Status

**Phase:** Research & Design
**Current Focus:** System architecture and component selection

## Design Constraints

- **No toxic or exotic materials** — all materials must be non-toxic and commonly available
- **Green to build** — minimal environmental impact in manufacturing
- **Maximum efficiency** — optimize collection, storage, and conversion

## System Overview

```
[Sun] → [Parabolic Dish] → [Sand Battery 500-600°C]
                                    ↓
         ┌──────────────────────────┼──────────────────────────┐
         ↓                          ↓                          ↓
    [Stirling]                   [ORC]                      [TEG]
    600→300°C                  300→100°C                  100→40°C
    15-25% eff                 10-15% eff                 3-5% eff
         ↓                          ↓                          ↓
         └──────────────────→ [Electricity] ←──────────────────┘
                                    ↓
                          [Hot Water / Heating]
```

**Overall solar-to-electric efficiency:** ~18%
**Total energy utilization (incl. thermal):** 60-80%

## Documentation

### Research
- [Solar Collection](docs/research/solar-collection.md) — Parabolic dish, Scheffler, Fresnel hybrid
- [Thermal Storage](docs/research/thermal-storage.md) — Sand battery, PCM, rock bed
- [Heat Conversion](docs/research/heat-conversion.md) — Stirling, ORC, Tesla turbine, TEG
- [Exploratory Concepts](docs/research/exploratory-concepts.md) — Unconventional first-principles ideas

### Design
- [System Architecture](docs/design/system-architecture.md) — Heat flow, staging, efficiency
- [Collector Design](docs/design/collector-design.md) — 1 m parabolic dish sizing and specifications
- [Materials](docs/design/materials.md) — Approved materials, sourcing
- [Specifications](docs/design/specifications.md) — Target performance, interfaces

### Computational
- [Tools](docs/computational/tools.md) — Software stack (FreeCAD, SolTrace, pymoo, etc.)
- [Workflows](docs/computational/workflows.md) — Optimization pipelines, simulation setup

## Directory Structure

```
solar-power-generator/
├── CLAUDE.md              # This file
├── docs/
│   ├── research/          # Deep dives on technologies
│   ├── design/            # Architecture, specs, materials
│   └── computational/     # Tools and workflows
├── src/                   # (Future) Simulation code
├── cad/                   # (Future) Parametric CAD files
├── simulations/           # (Future) CFD/FEA cases
└── fabrication/           # (Future) Manufacturing outputs
```

## Quick Reference

### Key Tools
- **CAD:** FreeCAD, CadQuery, OpenSCAD
- **Solar ray-tracing:** SolTrace, Tonatiuh, OTSun
- **Thermal CFD:** OpenFOAM, Elmer FEM
- **Optimization:** pymoo (NSGA-II), scipy.optimize
- **Gas properties:** CoolProp

## License

This project is dual-licensed:

- **Hardware, CAD, and documentation** (`docs/`, `cad/`, `fabrication/`, `simulations/`) — [CERN-OHL-S-2.0](LICENSE-CERN-OHL-S-2.0.txt)
- **Software and simulation code** (`src/`) — [GPL-3.0](LICENSE-GPL-3.0.txt)

### Key Decisions Made
- Cascade conversion (Stirling → ORC → TEG) rather than single engine
- Sand battery as primary storage (inspired by Polar Night Energy)
- Parabolic dish as primary collector (highest efficiency and temperature)
- Tesla turbine as ORC expander alternative (simpler fabrication)
