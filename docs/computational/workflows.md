# Computational Design Workflows

## Overview

This document describes the computational workflows for designing and optimizing each subsystem.

---

## Design Philosophy

1. **Parametric geometry** — all designs defined by code/parameters, not manual CAD
2. **Physics simulation** — ray-tracing, CFD, thermodynamic models validate designs
3. **Automated optimization** — optimizers drive the simulation loop to find Pareto-optimal designs
4. **Direct-to-fabrication** — output DXF (laser cutting), STL (3D printing), G-code (CNC), or dimensioned drawings

---

## Solar Collector Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Define params  │────▶│  Generate geom  │────▶│   Ray-trace     │
│  (focal, diam,  │     │  (FreeCAD/      │     │   (SolTrace)    │
│   rim angle)    │     │   OpenSCAD)     │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
       ┌─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Evaluate       │────▶│  Optimizer      │────▶│  Export DXF     │
│  efficiency     │     │  (pymoo)        │     │  for cutting    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 │ adjust parameters
                                 └─────────────────────────▶ (loop)
```

### Steps

1. Define reflector parameters (focal length, diameter, rim angle, segment count)
2. Generate geometry in FreeCAD/OpenSCAD
3. Export to SolTrace, run ray-trace simulation
4. Optimizer (pymoo) adjusts parameters to maximize optical efficiency
5. Export optimal design to DXF for mirror segment cutting

---

## Thermal Storage Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Define params  │────▶│  Generate geom  │────▶│   Mesh          │
│  (diameter,     │     │  (FreeCAD)      │     │   (Gmsh)        │
│   height, ins.) │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
       ┌─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CFD simulation │────▶│  Evaluate       │────▶│  Optimizer      │
│  (OpenFOAM or   │     │  heat loss,     │     │  (pymoo)        │
│   1D Python)    │     │  capacity       │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                 ┌───────────────────────┘
                                 │ build surrogate model
                                 ▼
                        ┌─────────────────┐
                        │  Gaussian Proc  │
                        │  surrogate      │
                        └─────────────────┘
```

### Steps

1. Define silo parameters (diameter, height, insulation layers, air channel geometry)
2. Generate geometry in FreeCAD, mesh with Gmsh
3. Run OpenFOAM `chtMultiRegionFoam` for conjugate heat transfer
4. Or use simplified 1D Python model for fast optimization
5. Optimizer minimizes heat loss while meeting capacity constraints
6. Build Gaussian Process surrogate model to reduce CFD runs

### Surrogate Modeling Approach

Full CFD is expensive. Use adaptive sampling:

1. Latin Hypercube sample of parameter space (50–100 points)
2. Run CFD for each sample
3. Train Gaussian Process regressor
4. Optimize on surrogate (fast)
5. Validate optimum with full CFD
6. Refine adaptively if needed

---

## Stirling Engine Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Define params  │────▶│  Thermodynamic  │────▶│  Calculate      │
│  (volumes,      │     │  model (Schmidt │     │  power, eff,    │
│   phase, regen) │     │  + losses)      │     │  size           │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
       ┌─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Multi-obj      │────▶│  Select from    │────▶│  Generate CAD   │
│  optimizer      │     │  Pareto front   │     │  (CadQuery)     │
│  (NSGA-II)      │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Export STEP    │
                                                │  for CNC        │
                                                └─────────────────┘
```

### Steps

1. Implement Schmidt isothermal analysis in Python
2. Add loss models: regenerator inefficiency, shuttle heat loss, conduction, flow friction
3. Validate against published experimental data (NASA GRC Stirling converters)
4. Define design variables: swept volumes, phase angle, regenerator dimensions, mean pressure
5. Run pymoo NSGA-II optimization (objectives: power, efficiency, size)
6. Generate Pareto front of optimal designs
7. Select preferred design, generate full CAD in CadQuery
8. Export STEP for CNC machining, STL for 3D printed components

---

## Example: Automated Stirling Optimization Loop

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.core.problem import Problem
import numpy as np
from stirling_model import simulate_stirling  # Custom implementation
import cadquery as cq

class StirlingProblem(Problem):
    def __init__(self):
        super().__init__(
            n_var=5,
            n_obj=3,  # Power, efficiency, size
            xl=[0.5e-4, 0.5e-4, 30, 0.02, 1e5],   # Lower bounds
            xu=[5e-4,   5e-4,   90, 0.10, 5e6]    # Upper bounds
        )

    def _evaluate(self, X, out):
        results = []
        for x in X:
            V_hot, V_cold, phase, L_regen, P_mean = x
            r = simulate_stirling(
                V_hot=V_hot, V_cold=V_cold,
                phase_angle=phase, regen_length=L_regen,
                mean_pressure=P_mean, T_hot=773, T_cold=323
            )
            results.append([-r['power'], -r['efficiency'], r['size']])
        out["F"] = np.array(results)

# Run optimization
algorithm = NSGA2(pop_size=100)
res = minimize(StirlingProblem(), algorithm, ('n_gen', 200), seed=1)

# Generate CAD for best design
best = res.X[0]
engine = generate_stirling_cad(best)  # CadQuery function
cq.exporters.export(engine, 'stirling_optimized.step')
```

---

## High-Fidelity Validation

For critical components, validate optimized designs with detailed CFD:

### Regenerator (OpenFOAM)

- Use porous media model (Darcy-Forchheimer)
- Oscillating flow boundary conditions
- Conjugate heat transfer with matrix

### Heat Exchanger (OpenFOAM)

- `chtMultiRegionFoam` solver
- Solid and fluid regions coupled
- Temperature-dependent properties

---

## Fabrication Output

| Format | Tool | Use |
|--------|------|-----|
| DXF | FreeCAD Draft / OpenSCAD | Laser cutting (mirror segments, sheet metal) |
| STL | Any CAD | 3D printing |
| STEP | FreeCAD / CadQuery | CNC machining |
| G-code | FreeCAD Path | Direct CNC control |
| PDF drawings | FreeCAD TechDraw | Manual fabrication |
