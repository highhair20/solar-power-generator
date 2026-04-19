# Thermal Storage — Subsystem CLAUDE.md

> Read the project-level CLAUDE.md first. This file adds thermal-storage-specific context.

## Subsystem Purpose

The thermal storage system stores heat from the solar collector in a large insulated
vessel and acts as a buffer between the intermittent solar input and the
continuously-operating power conversion system. It enables dispatchable power
generation beyond sunshine hours.

The storage medium is not yet finalised — the primary candidate is sand (granular
silica), chosen for low cost, high specific heat, non-toxicity, availability, and
stability at temperatures up to ~1000°C. Other candidates include rock beds and
phase-change materials (PCM). All models should be parameterised by material
properties rather than hardcoding sand-specific values.

---

## Physics Model

### Thermal Storage

**Energy stored:**
```
E_stored_J = m_medium × c_p × (T_storage_K - T_ref_K)
```

**Charging power (from collector):**
```
dE/dt = q_collector_W - q_discharge_W - Q_loss_W
```

**Temperature evolution (lumped capacitance model):**
```
dT_storage/dt = (q_collector_W - q_discharge_W - Q_loss_W) / (m_medium × c_p)
```

For a stratified model, discretize the storage into N vertical layers and solve
the 1D heat equation with upward flow during charge and downward flow during discharge.

**Thermal losses to environment:**
```
Q_loss_W = U_wall × A_surface × (T_storage_K - T_amb_K)
```
where `U_wall` is the overall heat loss coefficient of the insulated vessel [W/m²·K].

### Reference Material Properties (Silica Sand)

| Property               | Symbol       | Value       | Unit      |
|------------------------|--------------|-------------|-----------|
| Bulk density           | `rho_bulk`   | 1500–1600   | kg/m³     |
| Specific heat (avg)    | `c_p`        | 830–1000    | J/kg·K    |
| Thermal conductivity   | `k`          | 0.25–0.35   | W/m·K     |
| Max operating temp     | `T_max_K`    | ~1273       | K (1000°C)|
| Min operating temp     | `T_min_K`    | TBD         | K         |

**Note:** `c_p` varies with temperature. Use a temperature-dependent correlation
or a piecewise function — do not use a single constant above 400°C.

---

## Design Parameters (to be filled in)

| Parameter              | Symbol             | Value   | Unit   |
|------------------------|--------------------|---------|--------|
| Storage medium         | —                  | TBD     | —      |
| Medium mass            | `m_medium_kg`      | TBD     | kg     |
| Vessel volume          | `V_vessel_m3`      | TBD     | m³     |
| Vessel geometry        | —                  | TBD     | —      |
| Insulation thickness   | `t_insul_m`        | TBD     | m      |
| Insulation type        | —                  | TBD     | —      |
| Overall U-value        | `U_wall_W_m2K`     | TBD     | W/m²·K |
| Hot-side temperature   | `T_hot_K`          | TBD     | K      |
| Cold-side temperature  | `T_cold_K`         | TBD     | K      |
| Storage capacity       | `E_capacity_kWh`   | TBD     | kWh    |
| Target storage hours   | —                  | TBD     | h      |
| Charge/discharge rate  | —                  | TBD     | kW     |

---

## Inputs and Outputs (Interfaces)

### Inputs (from Solar Collector)
| Variable          | Description                        | Unit |
|-------------------|------------------------------------|------|
| `q_collector_W`   | Charging thermal power             | W    |
| `T_focal_K`       | Temperature of heat source         | K    |

### Outputs (to Power Conversion)
| Variable            | Description                                  | Unit |
|---------------------|----------------------------------------------|------|
| `T_storage_hot_K`   | Hot-side temperature available to engine     | K    |
| `T_storage_cold_K`  | Cold-side return temperature                 | K    |
| `q_discharge_W`     | Thermal power discharged to engine           | W    |
| `E_stored_kWh`      | Current stored energy (state of charge)      | kWh  |
| `SOC`               | State of charge (0 = empty, 1 = full)        | —    |

---

## Directory Structure

```
thermal-storage/
└── CLAUDE.md              ← This file

Python source → src/thermal_storage/
├── medium_properties.py   ← Temperature-dependent c_p, k, rho for storage medium
├── lumped_model.py        ← Single-node (lumped) thermal storage model
├── stratified_model.py    ← Multi-layer 1D stratified model (higher fidelity)
├── insulation.py          ← U-value calc for vessel walls (multi-layer insulation)
├── dispatch.py            ← Charge/discharge control logic
└── storage_system.py      ← Top-level model, selects lumped or stratified
```

---

## Modeling Guidance

**Start with the lumped model.** Use the stratified model only if temperature
stratification is critical to the power conversion interface (e.g., if the engine
requires a stable inlet temperature and collector input is highly variable).

**State of charge (SOC) limits:**
- Never let `SOC > 1.0` — charge power must be curtailed at full
- Never let `SOC < 0.0` — discharge must stop at empty
- Add a buffer: enforce `SOC_min = 0.05`, `SOC_max = 0.95` for safe operation

**Dispatch logic:**
- Charge when `q_collector_W > 0` and `SOC < SOC_max`
- Discharge to engine whenever `SOC > SOC_min` and engine demands heat
- If `q_collector_W` exceeds charge rate limit, curtail and log excess

**Insulation:**
Target `U_wall < 0.1 W/m²·K` for long-duration storage. Use mineral wool, refractory
ceramic fiber, or aerogel composites. Model as a series resistance network.

---

## Validation Targets

| Condition                          | Expected Result                                    |
|------------------------------------|----------------------------------------------------|
| Fully charged, no charge/discharge | SOC drops < 5% in 12 h (self-discharge)            |
| Charge at design power, 1 hour     | ΔT_storage matches energy balance within 1%        |
| Discharge at rated power           | `T_storage_hot_K` stays within ±20K of target     |
| Energy balance over full cycle     | Stored = Charged - Discharged - Losses ± 1%       |

Claude should flag any result outside these ranges and ask before proceeding.

---

## Failure Modes to Check

- `T_storage_K > T_max_K`: thermal runaway / medium degradation risk — hard stop
- `SOC > 1.0`: overcharge — curtail collector input immediately
- `SOC < 0.0`: overdischarge — stop engine input
- `Q_loss_W > 0.1 × q_collector_W` at steady state: insulation is undersized, warn
- Negative `q_discharge_W`: physically impossible — raise exception
