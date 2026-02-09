"""
Cavity Receiver — CadQuery Parametric Model

Generates the cylindrical cavity receiver with aperture, steel walls,
ceramic fiber insulation shell, and support arm mounting flange.

All dimensions from docs/design/collector-design.md.
"""

import math
import cadquery as cq

# ── Design Parameters ──────────────────────────────────────────────

# Cavity dimensions
APERTURE_DIAMETER = 40.0  # mm (4 cm)
CAVITY_INNER_DIAMETER = 70.0  # mm (7 cm)
CAVITY_DEPTH = 60.0  # mm (6 cm)
WALL_THICKNESS = 3.0  # mm (steel)
INSULATION_THICKNESS = 25.0  # mm (ceramic fiber blanket)

# Derived dimensions
CAVITY_OUTER_DIAMETER = CAVITY_INNER_DIAMETER + 2 * WALL_THICKNESS  # 76 mm
INSULATED_OUTER_DIAMETER = CAVITY_OUTER_DIAMETER + 2 * INSULATION_THICKNESS  # 126 mm
TOTAL_LENGTH = CAVITY_DEPTH + WALL_THICKNESS  # 63 mm (cavity + back wall)
INSULATED_LENGTH = TOTAL_LENGTH + INSULATION_THICKNESS  # 88 mm

# Mounting flange
FLANGE_OUTER_DIAMETER = INSULATED_OUTER_DIAMETER + 20.0  # 146 mm
FLANGE_THICKNESS = 4.0  # mm
FLANGE_BOLT_CIRCLE = (INSULATED_OUTER_DIAMETER + FLANGE_OUTER_DIAMETER) / 2  # bolt PCD
FLANGE_BOLT_DIAMETER = 6.0  # mm (M6 bolts)
FLANGE_NUM_BOLTS = 4

# Support arm
ARM_WIDTH = 25.0  # mm (square tube, matches frame)
ARM_WALL = 1.5  # mm
ARM_LENGTH = 100.0  # mm (stub from flange, connects to dish frame)


def make_cavity_shell() -> cq.Workplane:
    """Steel cavity body — cylinder with aperture opening at front.

    The cavity is a cup shape: closed at the back, open at the front
    with a reduced aperture.
    """
    # Outer cylinder (full cavity body)
    outer = (
        cq.Workplane("XY")
        .circle(CAVITY_OUTER_DIAMETER / 2)
        .extrude(TOTAL_LENGTH)
    )

    # Inner cavity bore (from the front face, full depth)
    inner = (
        cq.Workplane("XY")
        .circle(CAVITY_INNER_DIAMETER / 2)
        .extrude(CAVITY_DEPTH)
    )
    shell = outer.cut(inner)

    # Aperture — cut a hole in the front face (smaller than cavity ID)
    # The front face is at Z=0; cut through to make the aperture opening
    aperture_cut = (
        cq.Workplane("XY")
        .circle(APERTURE_DIAMETER / 2)
        .extrude(-WALL_THICKNESS)  # cut backward through front wall... but front is open
    )

    # Actually the front face is already open from the inner bore.
    # We need an aperture plate: an annular ring at Z=0 that restricts
    # the opening from CAVITY_INNER_DIAMETER down to APERTURE_DIAMETER.
    aperture_plate = (
        cq.Workplane("XY")
        .circle(CAVITY_INNER_DIAMETER / 2)
        .circle(APERTURE_DIAMETER / 2)
        .extrude(WALL_THICKNESS)
    )

    # The shell already has no front wall (inner bore goes to Z=0).
    # Add the aperture plate to create the restricted opening.
    shell = shell.union(aperture_plate)

    return shell


def make_insulation() -> cq.Workplane:
    """Ceramic fiber insulation shell around the cavity.

    Wraps the sides and back of the cavity. The front (aperture side)
    is left open.
    """
    # Outer insulation cylinder
    outer = (
        cq.Workplane("XY")
        .workplane(offset=-INSULATION_THICKNESS)  # extends behind back wall
        .circle(INSULATED_OUTER_DIAMETER / 2)
        .extrude(INSULATED_LENGTH)
    )

    # Cut out the cavity body volume (so insulation wraps around it)
    cavity_void = (
        cq.Workplane("XY")
        .circle(CAVITY_OUTER_DIAMETER / 2)
        .extrude(TOTAL_LENGTH)
    )
    insulation = outer.cut(cavity_void)

    # Cut the front face open at the aperture
    front_cut = (
        cq.Workplane("XY")
        .workplane(offset=TOTAL_LENGTH - 0.01)
        .circle(CAVITY_OUTER_DIAMETER / 2)
        .extrude(INSULATION_THICKNESS + 0.02)
    )
    insulation = insulation.cut(front_cut)

    return insulation


def make_mounting_flange() -> cq.Workplane:
    """Mounting flange at the back of the receiver for support arm attachment."""
    z_back = -INSULATION_THICKNESS

    flange = (
        cq.Workplane("XY")
        .workplane(offset=z_back - FLANGE_THICKNESS)
        .circle(FLANGE_OUTER_DIAMETER / 2)
        .circle(INSULATED_OUTER_DIAMETER / 2 - 5)  # center hole for heat transfer pipe
        .extrude(FLANGE_THICKNESS)
    )

    # Bolt holes
    for i in range(FLANGE_NUM_BOLTS):
        angle = i * (360.0 / FLANGE_NUM_BOLTS)
        x = (FLANGE_BOLT_CIRCLE / 2) * math.cos(math.radians(angle))
        y = (FLANGE_BOLT_CIRCLE / 2) * math.sin(math.radians(angle))
        bolt_hole = (
            cq.Workplane("XY")
            .workplane(offset=z_back - FLANGE_THICKNESS - 0.1)
            .center(x, y)
            .circle(FLANGE_BOLT_DIAMETER / 2)
            .extrude(FLANGE_THICKNESS + 0.2)
        )
        flange = flange.cut(bolt_hole)

    return flange


def make_support_arm_stub() -> cq.Workplane:
    """Short support arm stub extending from the mounting flange.

    This connects to the dish frame's receiver arm.
    """
    z_start = -INSULATION_THICKNESS - FLANGE_THICKNESS

    # Square tube arm extending downward (-Z direction, away from dish)
    outer = (
        cq.Workplane("XY")
        .workplane(offset=z_start)
        .rect(ARM_WIDTH, ARM_WIDTH)
        .extrude(-ARM_LENGTH)
    )
    inner = (
        cq.Workplane("XY")
        .workplane(offset=z_start + 0.1)
        .rect(ARM_WIDTH - 2 * ARM_WALL, ARM_WIDTH - 2 * ARM_WALL)
        .extrude(-(ARM_LENGTH + 0.2))
    )
    arm = outer.cut(inner)
    return arm


def make_receiver() -> cq.Workplane:
    """Complete receiver assembly: cavity + insulation + flange + arm stub."""
    receiver = make_cavity_shell()
    receiver = receiver.union(make_insulation())
    receiver = receiver.union(make_mounting_flange())
    receiver = receiver.union(make_support_arm_stub())
    return receiver


# ── Main: build and export when run directly ──────────────────────

if __name__ == "__main__":
    import os

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("Building cavity receiver...")
    receiver = make_receiver()
    cq.exporters.export(receiver, os.path.join(output_dir, "receiver.step"))
    cq.exporters.export(receiver, os.path.join(output_dir, "receiver.stl"))
    print("  → receiver.step, receiver.stl")

    print("Building cavity shell only...")
    cavity = make_cavity_shell()
    cq.exporters.export(cavity, os.path.join(output_dir, "cavity_shell.step"))
    print("  → cavity_shell.step")

    print("Done.")
