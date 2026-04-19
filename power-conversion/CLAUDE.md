# Power Conversion — Subsystem CLAUDE.md

> Read the project-level CLAUDE.md first. This file adds power-conversion-specific context.

## Subsystem Purpose

The power conversion system converts thermal energy discharged from thermal storage
into mechanical work and then electricity. It operates between the hot storage
temperature (high side) and ambient (low side).

The engine type is not yet finalised — the current design targets a cascade:
Stirling (600→300°C) → ORC (300→100°C) → TEG (100→40°C). Models should be
modular so individual stages can be swapped or removed.

---

## Engine Type Options

| Engine Type          | Pros                                               | Cons                                       | Typical η |
|----------------------|----------------------------------------------------|--------------------------------------------|-----------|
| **Stirling**         | External combustion, high η at small scale         | Expensive, sealing challenges, slow response | 25–40%  |
| **ORC (organic)**    | Low-to-medium temp, simple, off-the-shelf          | Lower η, working fluid cost/safety         | 10–20%   |
| **TEG**              | No moving parts, silent, reliable                  | Very low η                                 | 3–5%     |
| **Rankine (steam)**  | Mature technology, good at medium scale            | Requires water, boiler, condenser          | 20–35%   |
| **Brayton (air)**    | High temp operation, simple gas circuit            | Requires >700°C, less mature at small scale | 20–35%  |

**Current cascade design:**
- Stage 1: Stirling — 600→300°C, 15–25% efficiency
- Stage 2: ORC — 300→100°C, 10–15% efficiency
- Stage 3: TEG — 100→40°C, 3–5% efficiency

---

## Physics Model

### Thermodynamic Limits

**Carnot efficiency (theoretical maximum):**
```
eta_Carnot = 1 - T_cold_K / T_hot_K
```

**Practical (second-law) efficiency:**
```
eta_engine = eta_2nd_law × eta_Carnot
```
where `eta_2nd_law` is the fraction of Carnot achieved (typically 0.4–0.6 for real engines).

**Electrical output:**
```
P_elec_W = q_discharge_W × eta_engine
```

**Waste heat rejected:**
```
q_reject_W = q_discharge_W - P_elec_W
```
First law check: `q_discharge = P_elec + q_reject` — must always close within 0.1%.

### Engine Power Map

For realistic part-load behavior, use a power map: `eta = f(P/P_rated, T_hot, T_cold)`.
If a map is unavailable, use a quadratic part-load correction:
```
eta(PLR) = eta_design × (a + b×PLR + c×PLR²)
```
where PLR = P_actual / P_rated and [a, b, c] are engine-specific coefficients.

---

## Design Parameters (to be filled in)

| Parameter                | Symbol              | Value   | Unit   |
|--------------------------|---------------------|---------|--------|
| Rated thermal input      | `Q_rated_W`         | TBD     | W      |
| Rated electrical output  | `P_rated_W`         | TBD     | W      |
| Design η (gross)         | `eta_design`        | TBD     | —      |
| Parasitic losses         | `P_parasitic_W`     | TBD     | W      |
| Net electrical output    | `P_net_W`           | TBD     | W      |
| Hot-side design temp     | `T_hot_design_K`    | TBD     | K      |
| Cold-side design temp    | `T_cold_design_K`   | TBD     | K      |
| Min operating load       | `PLR_min`           | TBD     | —      |
| Start-up time            | `t_startup_s`       | TBD     | s      |
| Generator efficiency     | `eta_generator`     | TBD     | —      |

---

## Inputs and Outputs (Interfaces)

### Inputs (from Thermal Storage)
| Variable             | Description                              | Unit |
|----------------------|------------------------------------------|------|
| `T_storage_hot_K`    | Hot-side temperature from storage        | K    |
| `T_storage_cold_K`   | Cold-side return temperature             | K    |
| `q_discharge_W`      | Thermal power available from storage     | W    |

### Outputs (to Grid / System Level)
| Variable        | Description                        | Unit |
|-----------------|------------------------------------|------|
| `P_elec_W`      | Net electrical power output        | W    |
| `eta_engine`    | Net heat-to-electricity efficiency | —    |
| `q_reject_W`    | Waste heat to environment          | W    |
| `T_exhaust_K`   | Exhaust / cold-side temperature    | K    |

---

## Directory Structure

```
power-conversion/
├── CLAUDE.md              ← This file
└── cad/                   ← CadQuery CAD scripts
    ├── gamma_stirling.py  ← Gamma-type Stirling engine
    ├── free_piston_stirling.py ← Free-piston Stirling with linear alternator
    ├── cross_section.py   ← Cross-section visualisation
    ├── analysis.py        ← Thermodynamic analysis
    ├── optimize.py        ← NSGA-II optimisation
    └── output/            ← Generated STEP/STL (gitignored)

Python source → src/power_conversion/
├── stirling/              ← Stirling engine models and control
├── orc/                   ← ORC models and control
├── teg/                   ← TEG models
└── electrical/            ← Generator, inverter, parasitic losses
```

---

## Modeling Guidance

**Always compute Carnot efficiency first** as a sanity check before computing actual
output. If `eta_engine > eta_Carnot`, something is wrong — raise an exception.

**Parasitic loads:** Subtract blower fans, cooling pumps, control systems, etc. from
gross output to get net `P_elec_W`. Parasitics can be 5–15% of gross at design point.

**Cold-side temperature:** Do not assume constant `T_cold`. On hot days, ambient rises,
`T_cold` rises, `eta_Carnot` drops. Model this dependency explicitly.

**Start-up / shut-down:** The engine cannot ramp instantaneously. Model a start-up
delay (`t_startup_s`) during which thermal input is consumed but no electricity
is produced. This matters for daily cycle simulations.

**Working fluid (ORC):** Use CoolProp for fluid properties.
- ORC candidates: Toluene, MM (hexamethyldisiloxane), R245fa

---

## Validation Targets

| Condition                           | Expected Result                          |
|-------------------------------------|------------------------------------------|
| `T_hot` = design, `T_cold` = 25°C  | `eta_engine` within 5% of design spec   |
| First law balance                   | `q_discharge = P_elec + q_reject` ± 0.1%|
| `eta_engine < eta_Carnot`           | Always — exception if violated           |
| Part load at 50% PLR                | η degradation per manufacturer curve    |
| `T_hot_K` drops 10%                 | `P_elec_W` drops proportionally         |

Claude should flag any result outside these ranges and ask before proceeding.

---

## Failure Modes to Check

- `eta_engine >= eta_Carnot`: physically impossible — raise exception immediately
- `q_discharge_W = 0`: engine must shut down, `P_elec_W = 0`
- `T_hot_K < T_min_operating`: engine cannot start — set `P_elec_W = 0`, log event
- `PLR < PLR_min`: engine must cycle off rather than run below minimum load
- `P_elec_W < 0`: net negative power (parasitic > gross) — shut down engine
- First law imbalance > 0.1%: numerical error in model — raise exception
