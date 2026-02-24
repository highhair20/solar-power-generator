"""
Free-Piston Stirling Engine — Cross-Section Drawing

Generates a half-section view cut along the Z axis (through the YZ plane),
showing all internal components. Exports as SVG and DXF.
"""

import os
import cadquery as cq

from free_piston_stirling import (
    make_pressure_vessel,
    make_heater_head,
    make_displacer,
    make_power_piston,
    make_magnetic_spring_fixed,
    make_magnetic_spring_moving,
    make_alternator_stator,
    make_cooler,
    VESSEL_LENGTH,
    VESSEL_OD,
    HEATER_HEAD_LENGTH,
    HEATER_HEAD_OD,
    STATOR_OD,
    Z_DISPLACER,
    Z_PISTON,
    Z_ALTERNATOR,
    Z_MAG_FIXED,
    Z_MAG_MOVING,
    MAG_SPRING_LENGTH,
)


def make_cut_box() -> cq.Workplane:
    """Half-space box to cut components along the XZ plane (Y > 0 removed)."""
    size = max(VESSEL_LENGTH + HEATER_HEAD_LENGTH, STATOR_OD) * 2
    cut = (
        cq.Workplane("XY")
        .workplane(offset=-size / 2)
        .center(0, size / 2)
        .rect(size, size)
        .extrude(size)
    )
    return cut


def cut_half(shape: cq.Workplane) -> cq.Workplane:
    """Cut a shape in half along the XZ plane."""
    return shape.cut(make_cut_box())


def build_cross_section() -> cq.Assembly:
    """Build all components, cut each in half, and assemble."""
    assy = cq.Assembly(name="free_piston_cross_section")

    # Pressure vessel
    vessel = cut_half(make_pressure_vessel())
    assy.add(vessel, name="pressure_vessel", color=cq.Color("gray60"))

    # Heater head
    heater = cut_half(make_heater_head().translate((0, 0, VESSEL_LENGTH)))
    assy.add(heater, name="heater_head", color=cq.Color("firebrick"))

    # Displacer
    displacer = cut_half(make_displacer().translate((0, 0, Z_DISPLACER)))
    assy.add(displacer, name="displacer", color=cq.Color("orange"))

    # Magnetic spring — fixed
    mag_fixed = cut_half(make_magnetic_spring_fixed().translate((0, 0, Z_MAG_FIXED)))
    assy.add(mag_fixed, name="mag_spring_fixed", color=cq.Color("red3"))

    # Magnetic spring — moving
    mag_moving = cut_half(make_magnetic_spring_moving().translate((0, 0, Z_MAG_MOVING)))
    assy.add(mag_moving, name="mag_spring_moving", color=cq.Color("red1"))

    # Power piston + magnets
    piston = cut_half(make_power_piston().translate((0, 0, Z_PISTON)))
    assy.add(piston, name="power_piston", color=cq.Color("goldenrod"))

    # Alternator stator
    stator = cut_half(make_alternator_stator().translate((0, 0, Z_ALTERNATOR)))
    assy.add(stator, name="alternator_stator", color=cq.Color("darkgreen"))

    # Cooler fins
    cooler = cut_half(make_cooler().translate((0, 0, Z_MAG_MOVING + MAG_SPRING_LENGTH + 5)))
    assy.add(cooler, name="cooler", color=cq.Color("steelblue"))

    return assy


def export_svg_section():
    """Export a 2D projected SVG of the cross-section view from the front (looking along Y axis)."""
    print("Building cross-section components individually...")

    # Build each half-cut component as a compound for 2D projection
    parts = []

    print("  Cutting pressure vessel...")
    parts.append(cut_half(make_pressure_vessel()))

    print("  Cutting heater head...")
    parts.append(cut_half(make_heater_head().translate((0, 0, VESSEL_LENGTH))))

    print("  Cutting displacer...")
    parts.append(cut_half(make_displacer().translate((0, 0, Z_DISPLACER))))

    print("  Cutting magnetic springs...")
    parts.append(cut_half(make_magnetic_spring_fixed().translate((0, 0, Z_MAG_FIXED))))
    parts.append(cut_half(make_magnetic_spring_moving().translate((0, 0, Z_MAG_MOVING))))

    print("  Cutting power piston...")
    parts.append(cut_half(make_power_piston().translate((0, 0, Z_PISTON))))

    print("  Cutting alternator stator...")
    parts.append(cut_half(make_alternator_stator().translate((0, 0, Z_ALTERNATOR))))

    print("  Cutting cooler...")
    parts.append(cut_half(make_cooler().translate((0, 0, Z_MAG_MOVING + MAG_SPRING_LENGTH + 5))))

    # Combine all parts into one compound shape
    print("  Combining all parts...")
    combined = parts[0]
    for p in parts[1:]:
        combined = combined.union(p)

    return combined


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Export 3D cross-section as STEP
    print("Building 3D cross-section assembly...")
    assy = build_cross_section()

    step_path = os.path.join(output_dir, "free_piston_cross_section.step")
    print(f"Exporting STEP → {step_path}")
    assy.save(step_path)

    # Export 2D SVG projection (front view, looking along Y axis)
    print("\nBuilding 2D projection...")
    combined = export_svg_section()

    svg_path = os.path.join(output_dir, "free_piston_cross_section.svg")
    print(f"Exporting SVG → {svg_path}")
    cq.exporters.export(
        combined,
        svg_path,
        opt={
            "projectionDir": (0, -1, 0),  # looking along Y toward cut face
            "showHidden": False,
            "strokeWidth": 0.3,
            "width": 600,
            "height": 800,
        },
    )

    # Export combined half-cut as STL for easy viewing
    stl_path = os.path.join(output_dir, "free_piston_cross_section.stl")
    print(f"Exporting STL → {stl_path}")
    cq.exporters.export(combined, stl_path)

    print("\nDone. Files:")
    print(f"  STEP (3D, colored): {step_path}")
    print(f"  SVG (2D drawing):   {svg_path}")
    print(f"  STL (3D mesh):      {stl_path}")
