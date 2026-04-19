# Solar Power Generator

A solar thermal power system with heat storage for on-demand electricity generation.

## Project Status

**Phase:** Research & Design
**Current Focus:** System architecture and component selection

## Design Constraints

- **No toxic or exotic materials** — all materials must be non-toxic and commonly available
- **Green to build** — minimal environmental impact in manufacturing
- **Maximum efficiency** — optimise collection, storage, and conversion
- **CAD drawings** - no two components can occupy the same physical space at the same time

## System Overview

```
[Sun] → [Solar Collector] → [Thermal Storage 500-600°C]
                                       ↓
         ┌─────────────────────────────┼─────────────────────────────┐
         ↓                             ↓                             ↓
    [Stirling]                      [ORC]                         [TEG]
    600→300°C                     300→100°C                     100→40°C
    15-25% eff                    10-15% eff                     3-5% eff
         ↓                             ↓                             ↓
         └─────────────────→ [Electricity] ←─────────────────────────┘
                                       ↓
                             [Hot Water / Heating]
```

**Overall solar-to-electric efficiency:** ~18%
**Total energy utilisation (incl. thermal):** 60-80%

---

## Units & Conventions

| Quantity            | Unit                   | Notes                                          |
|---------------------|------------------------|------------------------------------------------|
| Temperature         | °C (calculations in K) | Always convert to Kelvin for thermodynamics    |
| Energy              | kWh or MJ              | MJ preferred for thermal storage calcs         |
| Power               | W or kW                | State which in variable names                  |
| Pressure            | kPa or bar             | Specify in context                             |
| Mass flow rate      | kg/s                   |                                                |
| Irradiance (DNI)    | W/m²                   | Direct Normal Irradiance                       |
| Efficiency          | dimensionless (0–1)    | Never use % in calculations                    |
| Area                | m²                     |                                                |
| Time                | s for simulation, h for reporting |                                   |

**Golden rule:** Include units in all variable names or docstrings. Never pass a bare
number between subsystems without labelling its unit.

---

## Interface Points Between Subsystems

These coupling variables must remain consistent across all three subsystems.

### Solar Collector → Thermal Storage
- `q_collector_W`: Thermal power delivered to storage [W]
- `T_focal_K`: Temperature at focal point / collector outlet [K]

### Thermal Storage → Power Conversion
- `T_storage_hot_K`: Hot-side temperature available to the engine [K]
- `T_storage_cold_K`: Cold-side temperature returned from engine [K]
- `q_discharge_W`: Thermal power discharged from storage to engine [W]

### Power Conversion → Grid
- `P_elec_W`: Electrical power output [W]
- `eta_engine`: Net heat-to-electricity efficiency (dimensionless)
- `q_reject_W`: Waste heat rejected to environment [W]

---

## Shared Constants

```python
SIGMA = 5.6704e-8       # Stefan-Boltzmann constant [W/m²·K⁴]
G_STC = 1000.0          # Irradiance at standard test conditions [W/m²]
T_AMB_K = 298.15        # Ambient temperature reference [K] (25°C)
C_P_AIR = 1005.0        # Specific heat of air [J/kg·K]
```

---

## Design Targets

| Metric                        | Target          |
|-------------------------------|-----------------|
| Peak electrical output        | TBD [kW]        |
| Daily energy yield            | TBD [kWh/day]   |
| Storage duration              | TBD [hours]     |
| System round-trip efficiency  | ~18%            |
| Design-point DNI              | 850 W/m²        |
| Ambient design temperature    | 25°C            |

---

## Directory Structure

```
solar-power-generator/
├── CLAUDE.md                  ← This file (project-level)
├── solar-collector/
│   ├── CLAUDE.md              ← Solar collector subsystem instructions
│   └── cad/                   ← CadQuery scripts (dish, receiver, assembly)
├── thermal-storage/
│   └── CLAUDE.md              ← Thermal storage subsystem instructions
├── power-conversion/
│   ├── CLAUDE.md              ← Power conversion subsystem instructions
│   └── cad/                   ← CadQuery scripts (Stirling engines)
├── src/                       ← Python source (packages use underscores)
│   ├── solar_collector/       ← Collector geometry, optics, tracking, sensors
│   ├── thermal_storage/       ← Storage models, dispatch, insulation
│   ├── power_conversion/      ← Stirling, ORC, TEG, generator models
│   └── utils/                 ← Shared code (sensors, simulation, supervisor)
├── docs/
│   ├── research/              ← Deep dives on technologies
│   ├── design/                ← Architecture, specs, materials
│   └── computational/         ← Tools and workflows
├── data/                      ← (Future) Weather, irradiance, soil properties
├── results/                   ← (Future) Simulation outputs, plots, reports
├── config/                    ← System configuration examples
└── fabrication/               ← (Future) Manufacturing outputs
```

**Python import convention:** Top-level component directories use hyphens (readable),
Python packages inside `src/` use underscores. Run simulations from the project root.
Import shared utilities via `from src.utils import ...`.

---

## Simulation Stack

- **Language:** Python 3.11+
- **Core libraries:** NumPy, SciPy, Matplotlib, Pandas
- **Thermodynamics:** CoolProp (fluid properties)
- **Solar / weather:** pvlib, TMY3 or EPW format
- **Optimisation:** pymoo (NSGA-II), scipy.optimize
- **CAD:** FreeCAD, CadQuery, OpenSCAD
- **Solar ray-tracing:** SolTrace, Tonatiuh, OTSun
- **Thermal CFD:** OpenFOAM, Elmer FEM
- **Testing:** pytest

---

## Coding Standards

- All functions must have docstrings with parameter units
- Use `snake_case` for variables and functions, `UPPER_CASE` for constants
- Every script must be runnable standalone with `python script.py`
- Never hardcode file paths — use `pathlib.Path` relative to project root
- Plots must save to `results/` and use consistent colour scheme:
  - Solar collector: `#F4A300` (amber)
  - Thermal storage: `#8B4513` (brown)
  - Power conversion: `#2E86AB` (blue)

---

## Verification Checklist

Before committing any subsystem change:
- [ ] Energy balance closes (inputs = outputs + losses) within 1%
- [ ] Output variables match the interface definitions above (correct units, names)
- [ ] Unit tests pass: `pytest tests/`
- [ ] Results are physically reasonable (no negative temperatures, η < 1, etc.)
- [ ] Any changed interface variable is updated in ALL connected subsystem models

---

## Key Decisions Made

- Cascade conversion (Stirling → ORC → TEG) rather than single engine
- Sand battery as primary storage candidate (inspired by Polar Night Energy)
- Parabolic dish as primary collector candidate (highest efficiency and temperature)
- Tesla turbine as ORC expander alternative (simpler fabrication)

---

## Key References

- Duffie & Beckman, *Solar Engineering of Thermal Processes* (4th ed.)
- Çengel & Boles, *Thermodynamics: An Engineering Approach*
- NREL SAM (System Advisor Model) — use for benchmarking simulation results
- IEA SolarPACES Task documentation for CSP performance standards

---

## License

This project is dual-licensed:

- **Hardware, CAD, and documentation** (`docs/`, `solar-collector/cad/`, `power-conversion/cad/`, `fabrication/`) — [CERN-OHL-S-2.0](LICENSE-CERN-OHL-S-2.0.txt)
- **Software and simulation code** (`src/`) — [GPL-3.0](LICENSE-GPL-3.0.txt)
