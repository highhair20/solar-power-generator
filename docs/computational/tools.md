# Computational Design Tools

## Overview

This document catalogs the open-source tools for computational design, simulation, and optimization. Inspired by LEAP 71's Noyron approach — physics-informed models generating optimized geometries directly exportable to manufacturing.

---

## Tool Stack Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      OPTIMIZATION LAYER                              │
│   pymoo (NSGA-II multi-objective) / scipy.optimize / DEAP           │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓↑
┌─────────────────────────────────────────────────────────────────────┐
│                      SIMULATION LAYER                                │
│  Solar: SolTrace/pysoltrace, Tonatiuh, OTSun                        │
│  Thermal: OpenFOAM, Elmer FEM, custom Python packed-bed models      │
│  Stirling: Python thermodynamic model + CoolProp, OpenFOAM (CFD)    │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓↑
┌─────────────────────────────────────────────────────────────────────┐
│                      GEOMETRY LAYER                                  │
│   FreeCAD (Python API) / CadQuery / OpenSCAD                        │
│   Gmsh (meshing for CFD/FEA)                                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      FABRICATION OUTPUT                              │
│   DXF (laser cut) | STL (3D print) | STEP (CNC) | G-code | Drawings │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Solar Collector Tools

| Tool | Purpose | License | Platform | Learning Curve |
|------|---------|---------|----------|----------------|
| **SolTrace** (NREL) | Monte Carlo ray-tracing for CSP | Open (LGPL) | Win/Lin/Mac | Intermediate |
| **pysoltrace** | Python bindings for SolTrace | Open | Python | Intermediate |
| **Tonatiuh** | Ray-tracing with 3D GUI | Open (GPL) | All | Beginner |
| **OTSun** | Ray-tracing integrated with FreeCAD | Open | All | Intermediate |
| **FreeCAD** | Parametric CAD, Python scriptable | Open (LGPL) | All | Moderate |
| **OpenSCAD** | Code-based geometry | Open (GPL) | All | Low (for programmers) |

### Key Metrics to Optimize

- Optical efficiency (intercepted power / incident power)
- Flux uniformity on receiver
- Tolerance sensitivity (efficiency degradation with surface errors)

---

## Thermal Storage Tools

| Tool | Purpose | License | Platform | Learning Curve |
|------|---------|---------|----------|----------------|
| **OpenFOAM** | CFD for packed-bed heat transfer, stratification | Open (GPL) | Lin/Win/Mac | Steep |
| **Elmer FEM** | Multiphysics FEA (Finnish, like Polar Night Energy) | Open (GPL) | All | Moderate |
| **SimScale** | Cloud CFD/FEA (free tier) | Freemium | Browser | Moderate |
| **Gmsh** | Parametric meshing | Open (GPL) | All | Moderate |
| **Python + NumPy** | 1D Schumann packed-bed model | Open | Python | Low |

### Key Metrics to Optimize

- Heat loss rate (W or W/m²)
- Storage capacity (kWh)
- Charge/discharge rate (kW)
- Cost (insulation thickness vs. performance)

---

## Stirling Engine Tools

| Tool | Purpose | License | Platform | Learning Curve |
|------|---------|---------|----------|----------------|
| **Python Stirling model** | Schmidt analysis + loss correlations | Custom/Open | Python | Moderate |
| **CoolProp** | Working gas thermophysical properties | Open (MIT) | Multi-language | Low |
| **OpenFOAM** | Regenerator CFD, heat exchanger CHT | Open (GPL) | Lin/Win/Mac | Steep |
| **CadQuery** | Python-native parametric CAD | Open (Apache) | Python | Low |
| **FreeCAD** | Full CAD with CNC path generation | Open (LGPL) | All | Moderate |
| **pymoo** | Multi-objective optimization | Open (Apache) | Python | Low |

### Key Metrics to Optimize

- Power output (W)
- Thermal efficiency (%)
- Size/weight
- Fabrication complexity

### Design Variables

- Swept volumes (hot/cold cylinders)
- Phase angle (alpha/beta/gamma configuration)
- Regenerator: length, diameter, porosity, wire diameter
- Dead volumes
- Mean pressure
- Working gas (air, N₂, He)
- Heat exchanger surface area

---

## Optimization Tools

| Tool | Purpose | License | Best For |
|------|---------|---------|----------|
| **scipy.optimize** | Single-objective optimization | BSD | Simple problems |
| **pymoo** | Multi-objective (NSGA-II, NSGA-III) | Apache | Pareto-optimal exploration |
| **DEAP** | Evolutionary algorithms | LGPL | Custom genetic algorithms |
| **OpenMDAO** | Multidisciplinary optimization | Apache | Complex coupled systems |
| **Dakota** | Uncertainty quantification, optimization | LGPL | Robust optimization |

---

## Meshing Tools

| Tool | Purpose | License |
|------|---------|---------|
| **Gmsh** | Parametric 2D/3D meshing, Python API | GPL |
| **snappyHexMesh** | OpenFOAM hex-dominant meshing | GPL |
| **Salome-Meca** | Full pre/post-processor with meshing | LGPL |

---

## CAD Tools

| Tool | Strengths | Export Formats |
|------|-----------|----------------|
| **FreeCAD** | Full parametric CAD, Python API, FEM workbench | STEP, STL, DXF, IGES |
| **CadQuery** | Python-native, Jupyter integration, STEP export | STEP, STL |
| **OpenSCAD** | Code-based, version control friendly | STL, DXF, SVG |
| **Blender** | Complex geometry, visualization | STL, many formats |

---

## Recommended Minimum Toolchain

For a complete computational design pipeline with minimal setup:

1. **FreeCAD** — parametric CAD for all components
2. **SolTrace + pysoltrace** — solar collector ray-tracing
3. **Python** — thermal storage model (1D packed-bed), Stirling thermodynamic model
4. **CoolProp** — gas properties for Stirling
5. **pymoo** — multi-objective optimization
6. **Gmsh** — meshing (when CFD needed)
7. **OpenFOAM** — high-fidelity CFD validation (optional, for critical components)

All tools are **open-source**, **cross-platform**, and can be **scripted in Python** for automated design exploration.
