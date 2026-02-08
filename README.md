# Solar Power Generator

A concentrated solar power (CSP) system with thermal storage and hybrid cascade conversion.

## Overview

This project aims to build a solar thermal power generation system that:
- Collects solar energy using concentrated solar power (Scheffler reflector or parabolic dish)
- Stores energy as heat in a sand battery (500-600°C)
- Converts stored heat to electricity using a three-stage cascade:
  - Stage 1: Stirling engine (600°C → 300°C)
  - Stage 2: ORC or Tesla turbine (300°C → 100°C)
  - Stage 3: TEG (100°C → 40°C)

## Design Constraints

- **Non-toxic materials only**: No exotic or hazardous substances
- **Green to build**: Environmentally responsible manufacturing
- **Maximum efficiency**: Optimized at every stage

## Project Structure

```
├── docs/
│   ├── research/      # Research notes and findings
│   ├── design/        # System design documentation
│   └── computational/ # Simulation and optimization workflows
├── src/
│   ├── collector/     # Solar collector control and sensors
│   ├── storage/       # Thermal storage monitoring
│   ├── conversion/    # Heat-to-electricity conversion
│   ├── electrical/    # Power output management
│   ├── common/        # Shared utilities and base classes
│   ├── simulation/    # Physics simulation modules
│   └── supervisor/    # System state machine and safety
└── config/            # Configuration files (future)
```

## Status

Currently in research and early development phase.

## License

This project is dual-licensed:

- **Hardware, CAD, and documentation** — [CERN-OHL-S-2.0](LICENSE-CERN-OHL-S-2.0.txt)
- **Software and simulation code** — [GPL-3.0](LICENSE-GPL-3.0.txt)
