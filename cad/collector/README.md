# Collector CAD Scripts

CadQuery parametric models for the 1 m parabolic dish collector and cavity receiver.

## Setup

```bash
pip install cadquery
```

## Usage

Export all models (STEP, STL, DXF) to `output/`:

```bash
python cad/collector/export.py
```

Or run individual scripts:

```bash
python cad/collector/dish.py       # Dish + backup structure + flat petal pattern
python cad/collector/receiver.py   # Cavity receiver + insulation
python cad/collector/assembly.py   # Full assembly (dish + receiver at focal point)
```

## Output Files

| File | Format | Description |
|------|--------|-------------|
| `dish` | STEP, STL | Full parabolic dish (360° shell) |
| `backup_structure` | STEP, STL | Hub + 8 ribs + rim ring |
| `petal_flat_pattern` | STEP, STL, DXF | Unfolded single petal for laser cutting |
| `receiver` | STEP, STL | Complete receiver (cavity + insulation + flange) |
| `cavity_shell` | STEP | Steel cavity body only |
| `collector_assembly` | STEP | All components assembled |

## Parameters

All dimensions are defined as constants at the top of each script and match
[`docs/design/collector-design.md`](../../docs/design/collector-design.md). Key values:

| Parameter | Value | Script |
|-----------|-------|--------|
| Dish diameter | 1000 mm | `dish.py` |
| Focal length | 600 mm | `dish.py` |
| Petals | 8 | `dish.py` |
| Receiver aperture | 40 mm | `receiver.py` |
| Cavity inner diameter | 70 mm | `receiver.py` |
| Cavity depth | 60 mm | `receiver.py` |
