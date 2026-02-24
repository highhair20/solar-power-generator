"""
Gamma-Type Stirling Engine — CadQuery Parametric Model

Generates a conceptual/dimensional model of a gamma-type Stirling engine
with separate hot (displacer) and cold (power) cylinders connected by
a passage with regenerator housing.

Sized for ~200W electrical output from ~550W thermal input (1m dish).
"""

import math
import cadquery as cq

# ── Design Parameters ──────────────────────────────────────────────

# Hot cylinder (displacer)
HOT_BORE = 80.0        # mm — displacer cylinder inner diameter
HOT_LENGTH = 100.0     # mm — displacer cylinder length
HOT_WALL = 3.0         # mm — wall thickness

# Cold cylinder (power piston)
COLD_BORE = 60.0       # mm — power cylinder inner diameter
COLD_LENGTH = 80.0     # mm — power cylinder length
COLD_WALL = 3.0        # mm — wall thickness

# Heater head (hot-end cap)
HEATER_HEAD_THICKNESS = 5.0   # mm — thicker cap for heat absorption
HEATER_HEAD_FIN_COUNT = 12    # radial fins on exterior
HEATER_HEAD_FIN_HEIGHT = 15.0 # mm
HEATER_HEAD_FIN_THICKNESS = 2.0  # mm

# Cooler fins (cold-end)
COOLER_FIN_COUNT = 16
COOLER_FIN_HEIGHT = 12.0  # mm
COOLER_FIN_THICKNESS = 1.5  # mm
COOLER_FIN_SPACING = 4.0  # mm — axial spacing
COOLER_NUM_ROWS = 5  # rows of fins along cylinder axis

# Displacer piston
DISPLACER_OD = HOT_BORE - 2.0   # mm — clearance to bore
DISPLACER_LENGTH = 60.0          # mm
DISPLACER_WALL = 1.5             # mm — thin-walled, lightweight

# Power piston
PISTON_OD = COLD_BORE - 1.0     # mm — tighter fit
PISTON_LENGTH = 30.0             # mm
PISTON_WALL = 5.0                # mm — solid piston

# Connecting passage
PASSAGE_DIAMETER = 25.0   # mm — inner diameter
PASSAGE_WALL = 2.0        # mm
REGEN_LENGTH = 40.0       # mm — regenerator housing section

# Crankshaft and flywheel
FLYWHEEL_DIAMETER = 150.0  # mm
FLYWHEEL_THICKNESS = 15.0  # mm
CRANK_RADIUS = 15.0        # mm — stroke / 2
CRANK_SHAFT_DIA = 15.0     # mm
CRANK_PIN_DIA = 10.0       # mm
CRANK_LENGTH = 120.0       # mm — between bearings

# Layout — offset between cylinder axes
CYLINDER_OFFSET = 100.0  # mm — center-to-center distance (X direction)


# ── Component Functions ────────────────────────────────────────────

def make_hot_cylinder() -> cq.Workplane:
    """Displacer cylinder with heater head (hot-end cap with heat fins).

    Cylinder axis along Z. Open at bottom (Z=0), heater head at top.
    """
    od = HOT_BORE + 2 * HOT_WALL

    # Cylinder tube
    outer = cq.Workplane("XY").circle(od / 2).extrude(HOT_LENGTH)
    inner = cq.Workplane("XY").circle(HOT_BORE / 2).extrude(HOT_LENGTH)
    cylinder = outer.cut(inner)

    # Heater head — solid cap at top
    head = (
        cq.Workplane("XY")
        .workplane(offset=HOT_LENGTH)
        .circle(od / 2)
        .extrude(HEATER_HEAD_THICKNESS)
    )
    cylinder = cylinder.union(head)

    # Heater head fins — radial plates on the top cap exterior
    for i in range(HEATER_HEAD_FIN_COUNT):
        angle = i * (360.0 / HEATER_HEAD_FIN_COUNT)
        angle_rad = math.radians(angle)
        r_inner = od / 2
        r_outer = od / 2 + HEATER_HEAD_FIN_HEIGHT

        # Fin as a thin box, positioned radially
        fin = (
            cq.Workplane("XY")
            .workplane(offset=HOT_LENGTH)
            .center(
                (r_inner + r_outer) / 2 * math.cos(angle_rad),
                (r_inner + r_outer) / 2 * math.sin(angle_rad),
            )
            .rect(HEATER_HEAD_FIN_HEIGHT, HEATER_HEAD_FIN_THICKNESS)
            .extrude(HEATER_HEAD_THICKNESS)
        )
        fin = fin.rotate(
            (0, 0, 0), (0, 0, 1), angle
        )
        # Simpler approach: build fin at angle using transformed workplane
        # Actually, let's rebuild the fin properly
        pass

    # Simpler heater fins: concentric ring fins on top
    for i in range(3):
        z_offset = HOT_LENGTH + HEATER_HEAD_THICKNESS
        ring_r = od / 2 + 5 + i * 6
        ring = (
            cq.Workplane("XY")
            .workplane(offset=z_offset)
            .circle(ring_r + 1)
            .circle(ring_r)
            .extrude(HEATER_HEAD_FIN_HEIGHT)
        )
        cylinder = cylinder.union(ring)

    return cylinder


def make_cold_cylinder() -> cq.Workplane:
    """Power cylinder with cooler fins on the exterior.

    Positioned offset from hot cylinder along X axis.
    Cylinder axis along Z. Open at top (Z=COLD_LENGTH), closed at bottom.
    """
    od = COLD_BORE + 2 * COLD_WALL

    # Cylinder tube
    outer = cq.Workplane("XY").circle(od / 2).extrude(COLD_LENGTH)
    inner = (
        cq.Workplane("XY")
        .circle(COLD_BORE / 2)
        .extrude(COLD_LENGTH)
    )
    cylinder = outer.cut(inner)

    # Bottom cap (closed end)
    cap = (
        cq.Workplane("XY")
        .workplane(offset=-COLD_WALL)
        .circle(od / 2)
        .extrude(COLD_WALL)
    )
    cylinder = cylinder.union(cap)

    # Cooler fins — annular rings along the cylinder exterior
    for row in range(COOLER_NUM_ROWS):
        z = 10 + row * (COOLER_FIN_THICKNESS + COOLER_FIN_SPACING)
        fin = (
            cq.Workplane("XY")
            .workplane(offset=z)
            .circle(od / 2 + COOLER_FIN_HEIGHT)
            .circle(od / 2)
            .extrude(COOLER_FIN_THICKNESS)
        )
        cylinder = cylinder.union(fin)

    return cylinder


def make_displacer() -> cq.Workplane:
    """Lightweight displacer piston — thin-walled hollow cylinder.

    Positioned inside the hot cylinder, shown at mid-stroke.
    """
    outer = cq.Workplane("XY").circle(DISPLACER_OD / 2).extrude(DISPLACER_LENGTH)
    inner = (
        cq.Workplane("XY")
        .circle(DISPLACER_OD / 2 - DISPLACER_WALL)
        .extrude(DISPLACER_LENGTH)
    )
    displacer = outer.cut(inner)

    # Top and bottom caps
    top_cap = (
        cq.Workplane("XY")
        .workplane(offset=DISPLACER_LENGTH)
        .circle(DISPLACER_OD / 2)
        .extrude(DISPLACER_WALL)
    )
    bottom_cap = (
        cq.Workplane("XY")
        .workplane(offset=-DISPLACER_WALL)
        .circle(DISPLACER_OD / 2)
        .extrude(DISPLACER_WALL)
    )
    displacer = displacer.union(top_cap).union(bottom_cap)

    # Displacer rod (connects to crankshaft through power piston)
    rod_dia = 8.0
    rod_length = HOT_LENGTH + 50  # extends below hot cylinder
    rod = (
        cq.Workplane("XY")
        .workplane(offset=-DISPLACER_WALL)
        .circle(rod_dia / 2)
        .extrude(-rod_length)
    )
    displacer = displacer.union(rod)

    return displacer


def make_power_piston() -> cq.Workplane:
    """Power piston — solid cylindrical piston with connecting rod stub."""
    piston = cq.Workplane("XY").circle(PISTON_OD / 2).extrude(PISTON_LENGTH)

    # Wrist pin boss (simplified as a through-hole)
    pin_hole = (
        cq.Workplane("XZ")
        .workplane(offset=0)
        .center(0, PISTON_LENGTH / 2)
        .circle(CRANK_PIN_DIA / 2)
        .extrude(PISTON_OD)
    )
    piston = piston.cut(pin_hole.translate((0, -PISTON_OD / 2, 0)))

    # Connecting rod stub
    rod_dia = 10.0
    rod_length = 60.0
    rod = (
        cq.Workplane("XY")
        .workplane(offset=-rod_length)
        .circle(rod_dia / 2)
        .extrude(rod_length)
    )
    piston = piston.union(rod)

    return piston


def make_connecting_passage() -> cq.Workplane:
    """Tube connecting hot and cold cylinders, with regenerator housing.

    Runs horizontally (along X) between the two cylinder positions.
    Includes a widened regenerator section in the middle.
    """
    od = PASSAGE_DIAMETER + 2 * PASSAGE_WALL
    passage_length = CYLINDER_OFFSET

    # Main tube
    outer = cq.Workplane("YZ").circle(od / 2).extrude(passage_length)
    inner = cq.Workplane("YZ").circle(PASSAGE_DIAMETER / 2).extrude(passage_length)
    tube = outer.cut(inner)

    # Regenerator housing — wider section in the middle
    regen_od = od + 10
    regen_start = (passage_length - REGEN_LENGTH) / 2
    regen_outer = (
        cq.Workplane("YZ")
        .workplane(offset=regen_start)
        .circle(regen_od / 2)
        .extrude(REGEN_LENGTH)
    )
    regen_inner = (
        cq.Workplane("YZ")
        .workplane(offset=regen_start)
        .circle(regen_od / 2 - PASSAGE_WALL)
        .extrude(REGEN_LENGTH)
    )
    regen_housing = regen_outer.cut(regen_inner)
    tube = tube.union(regen_housing)

    return tube


def make_crankshaft() -> cq.Workplane:
    """Crankshaft with flywheel — simplified representation.

    Shaft runs along Y axis, flywheel on one end.
    """
    # Main shaft
    shaft = (
        cq.Workplane("XZ")
        .circle(CRANK_SHAFT_DIA / 2)
        .extrude(CRANK_LENGTH)
    )

    # Crank throws (two, 90° apart for gamma config)
    for i, angle in enumerate([0, 90]):
        angle_rad = math.radians(angle)
        y_pos = 30 + i * 60  # positions along shaft
        throw_x = CRANK_RADIUS * math.cos(angle_rad)
        throw_z = CRANK_RADIUS * math.sin(angle_rad)

        # Crank web
        web = (
            cq.Workplane("XZ")
            .workplane(offset=y_pos)
            .center(0, 0)
            .rect(CRANK_RADIUS * 2 + CRANK_PIN_DIA, CRANK_PIN_DIA + 4)
            .extrude(8)
        )
        web = web.rotate((0, 0, 0), (0, 1, 0), angle)
        shaft = shaft.union(web)

        # Crank pin
        pin = (
            cq.Workplane("XZ")
            .workplane(offset=y_pos)
            .center(throw_x, throw_z)
            .circle(CRANK_PIN_DIA / 2)
            .extrude(8)
        )
        shaft = shaft.union(pin)

    # Flywheel
    flywheel = (
        cq.Workplane("XZ")
        .workplane(offset=CRANK_LENGTH)
        .circle(FLYWHEEL_DIAMETER / 2)
        .circle(CRANK_SHAFT_DIA / 2)
        .extrude(FLYWHEEL_THICKNESS)
    )
    shaft = shaft.union(flywheel)

    return shaft


def make_gamma_stirling() -> cq.Assembly:
    """Full gamma-type Stirling engine assembly.

    Layout:
    - Hot cylinder centered at origin, axis along Z
    - Cold cylinder offset along X by CYLINDER_OFFSET
    - Connecting passage at mid-height between them
    - Crankshaft below both cylinders along Y axis
    """
    assy = cq.Assembly(name="gamma_stirling")

    print("  Building hot cylinder (displacer)...")
    assy.add(make_hot_cylinder(), name="hot_cylinder", color=cq.Color("firebrick"))

    print("  Building cold cylinder (power)...")
    cold = make_cold_cylinder()
    cold = cold.translate((CYLINDER_OFFSET, 0, 0))
    assy.add(cold, name="cold_cylinder", color=cq.Color("steelblue"))

    print("  Building displacer piston...")
    displacer = make_displacer()
    # Position at mid-stroke inside hot cylinder
    displacer_z = (HOT_LENGTH - DISPLACER_LENGTH) / 2
    displacer = displacer.translate((0, 0, displacer_z))
    assy.add(displacer, name="displacer", color=cq.Color("orange"))

    print("  Building power piston...")
    piston = make_power_piston()
    # Position at mid-stroke inside cold cylinder
    piston_z = (COLD_LENGTH - PISTON_LENGTH) / 2
    piston = piston.translate((CYLINDER_OFFSET, 0, piston_z))
    assy.add(piston, name="power_piston", color=cq.Color("goldenrod"))

    print("  Building connecting passage + regenerator...")
    passage = make_connecting_passage()
    # Position at mid-height of hot cylinder
    passage_z = HOT_LENGTH * 0.4
    passage = passage.translate((0, 0, passage_z))
    assy.add(passage, name="connecting_passage", color=cq.Color("gray50"))

    print("  Building crankshaft + flywheel...")
    crank = make_crankshaft()
    # Position below both cylinders
    crank_z = -40
    crank_y = -CRANK_LENGTH / 2
    crank = crank.translate((CYLINDER_OFFSET / 2, crank_y, crank_z))
    assy.add(crank, name="crankshaft", color=cq.Color("gray30"))

    return assy


# ── Main: build and export when run directly ──────────────────────

if __name__ == "__main__":
    import os

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("Building gamma-type Stirling engine...")
    assembly = make_gamma_stirling()

    print("Exporting STEP...")
    assembly.save(os.path.join(output_dir, "gamma_stirling.step"))
    print("  → gamma_stirling.step")

    # Also export individual STL for visualization
    print("Exporting STL of hot cylinder...")
    cq.exporters.export(make_hot_cylinder(), os.path.join(output_dir, "gamma_hot_cylinder.stl"))
    print("  → gamma_hot_cylinder.stl")

    print("Done.")
