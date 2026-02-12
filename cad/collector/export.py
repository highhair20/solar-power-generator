"""
Export Utility — Run all collector models and export to output directory.

Exports:
  - STEP files (3D models for CNC / further CAD work)
  - STL files (visualization / 3D printing)
  - DXF files (2D flat patterns for laser cutting)

Output directory: cad/collector/output/
"""

import os
import sys

import cadquery as cq

# Ensure this script can import sibling modules
sys.path.insert(0, os.path.dirname(__file__))

from dish import (
    make_dish,
    make_backup_structure,
    make_petal_flat_pattern,
    make_petal_flat_pattern_2d,
)
from receiver import make_receiver, make_cavity_shell
from assembly import make_assembly
from faceted_dish import make_faceted_dish, make_frame, make_faceted_assembly
from faceted_dish_octagon import (
    make_faceted_dish_octagon,
    make_frame as make_frame_octagon,
    make_faceted_assembly_octagon,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def export_step(workplane: cq.Workplane, name: str):
    path = os.path.join(OUTPUT_DIR, f"{name}.step")
    cq.exporters.export(workplane, path)
    print(f"  STEP → {path}")


def export_stl(workplane: cq.Workplane, name: str):
    path = os.path.join(OUTPUT_DIR, f"{name}.stl")
    cq.exporters.export(workplane, path)
    print(f"  STL  → {path}")


def export_dxf(workplane: cq.Workplane, name: str):
    path = os.path.join(OUTPUT_DIR, f"{name}.dxf")
    cq.exporters.export(workplane, path)
    print(f"  DXF  → {path}")


def export_assembly_step(assembly: cq.Assembly, name: str):
    path = os.path.join(OUTPUT_DIR, f"{name}.step")
    assembly.save(path)
    print(f"  STEP → {path}")


def export_all():
    """Run all models and export all formats."""
    ensure_output_dir()

    # ── Dish ──────────────────────────────────────────────────────
    print("\n[1/7] Parabolic dish (8 petals)...")
    dish = make_dish()
    export_step(dish, "dish")
    export_stl(dish, "dish")

    # ── Backup structure ──────────────────────────────────────────
    print("\n[2/7] Backup structure (hub + ribs + rim ring)...")
    structure = make_backup_structure()
    export_step(structure, "backup_structure")
    export_stl(structure, "backup_structure")

    # ── Petal flat pattern ────────────────────────────────────────
    print("\n[3/7] Petal flat pattern (for cutting)...")
    petal_3d = make_petal_flat_pattern(0)
    export_step(petal_3d, "petal_flat_pattern")
    export_stl(petal_3d, "petal_flat_pattern")

    petal_2d = make_petal_flat_pattern_2d(0)
    export_dxf(petal_2d, "petal_flat_pattern")

    # ── Receiver ──────────────────────────────────────────────────
    print("\n[4/7] Cavity receiver...")
    receiver = make_receiver()
    export_step(receiver, "receiver")
    export_stl(receiver, "receiver")

    cavity = make_cavity_shell()
    export_step(cavity, "cavity_shell")

    # ── Full assembly ─────────────────────────────────────────────
    print("\n[5/7] Full collector assembly...")
    assembly = make_assembly()
    # Assembly uses .save() instead of cq.exporters.export()
    path = os.path.join(OUTPUT_DIR, "collector_assembly.step")
    assembly.save(path)
    print(f"  STEP → {path}")

    # ── Faceted dish variant (hexagonal) ─────────────────────────
    print("\n[6/7] Faceted dish (hexagonal)...")
    faceted_dish = make_faceted_dish()
    export_assembly_step(faceted_dish, "faceted_dish")

    frame = make_frame()
    export_step(frame, "faceted_frame")
    export_stl(frame, "faceted_frame")

    faceted_assy = make_faceted_assembly()
    export_assembly_step(faceted_assy, "faceted_assembly")

    # ── Faceted dish variant (octagon+square) ──────────────────
    print("\n[7/7] Faceted dish (octagon+square)...")
    oct_dish = make_faceted_dish_octagon()
    export_assembly_step(oct_dish, "octagon_dish")

    oct_frame = make_frame_octagon()
    export_step(oct_frame, "octagon_frame")
    export_stl(oct_frame, "octagon_frame")

    oct_assy = make_faceted_assembly_octagon()
    export_assembly_step(oct_assy, "octagon_assembly")

    print("\n✓ All exports complete.")
    print(f"  Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    export_all()
