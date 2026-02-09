"""
Collector Assembly — CadQuery Parametric Model

Combines the parabolic dish (petals + backup structure) with the cavity
receiver positioned at the focal point, connected by support arms.

All dimensions from docs/design/collector-design.md.
"""

import math
import cadquery as cq

from dish import (
    make_dish,
    make_backup_structure,
    DISH_RADIUS,
    FOCAL_LENGTH,
    RIB_WIDTH,
    RIB_WALL,
    paraboloid_z,
)
from receiver import make_receiver, INSULATION_THICKNESS, FLANGE_THICKNESS

# ── Assembly Parameters ────────────────────────────────────────────

# Support arms: 3 arms from rim to receiver (tripod configuration)
NUM_SUPPORT_ARMS = 3
SUPPORT_ARM_WIDTH = 20.0  # mm (round tube OD)
SUPPORT_ARM_WALL = 1.5  # mm

# Receiver position
RECEIVER_Z = FOCAL_LENGTH  # 600 mm from vertex (along Z axis)


def make_support_arm(arm_index: int = 0) -> cq.Workplane:
    """Single support arm from dish rim to focal point area.

    Arms attach at the rim ring and converge at the receiver position.
    """
    angle = arm_index * (360.0 / NUM_SUPPORT_ARMS)
    angle_rad = math.radians(angle)

    # Rim attachment point
    rim_r = DISH_RADIUS * 0.95  # slightly inside rim
    rim_z = paraboloid_z(rim_r)
    rim_x = rim_r * math.cos(angle_rad)
    rim_y = rim_r * math.sin(angle_rad)

    # Receiver attachment point (near focal point)
    recv_offset = 30.0  # mm offset from center at receiver end
    recv_x = recv_offset * math.cos(angle_rad)
    recv_y = recv_offset * math.sin(angle_rad)
    recv_z = RECEIVER_Z

    # Arm as a cylinder from rim to receiver
    arm_length = math.sqrt(
        (recv_x - rim_x) ** 2 + (recv_y - rim_y) ** 2 + (recv_z - rim_z) ** 2
    )

    # Direction vector
    dx = recv_x - rim_x
    dy = recv_y - rim_y
    dz = recv_z - rim_z

    # Build arm along Z axis then orient it
    outer = cq.Workplane("XY").circle(SUPPORT_ARM_WIDTH / 2).extrude(arm_length)
    inner = cq.Workplane("XY").circle(SUPPORT_ARM_WIDTH / 2 - SUPPORT_ARM_WALL).extrude(arm_length)
    arm = outer.cut(inner)

    # Calculate rotation to align Z-axis with the arm direction
    arm_dir_len = arm_length
    # Elevation angle from XY plane
    elev = math.degrees(math.asin(dz / arm_dir_len))
    # Azimuth angle in XY plane
    azim = math.degrees(math.atan2(dy, dx))

    # Rotate: first tilt from vertical (Z) to the elevation, then rotate in azimuth
    arm = arm.rotate((0, 0, 0), (0, 1, 0), 90 - elev)
    arm = arm.rotate((0, 0, 0), (0, 0, 1), azim)

    # Translate to rim attachment point
    arm = arm.translate((rim_x, rim_y, rim_z))

    return arm


def make_support_arms() -> cq.Workplane:
    """All support arms (tripod configuration)."""
    arms = make_support_arm(0)
    for i in range(1, NUM_SUPPORT_ARMS):
        arms = arms.union(make_support_arm(i))
    return arms


def make_assembly() -> cq.Workplane:
    """Full collector assembly: dish + structure + arms + receiver."""
    print("  Building dish petals...")
    dish = make_dish()

    print("  Building backup structure...")
    structure = make_backup_structure()

    print("  Building support arms...")
    arms = make_support_arms()

    print("  Building receiver...")
    receiver = make_receiver()
    # Position receiver at focal point, aperture facing down toward dish (toward -Z)
    # Receiver is built with aperture at Z=0, cavity extending in +Z
    # We need aperture at focal point facing the dish, so rotate 180° around X
    receiver = receiver.rotate((0, 0, 0), (1, 0, 0), 180)
    # Now aperture faces -Z (toward dish). Translate to focal point.
    receiver = receiver.translate((0, 0, RECEIVER_Z))

    print("  Combining assembly...")
    assembly = dish.union(structure)
    assembly = assembly.union(arms)
    assembly = assembly.union(receiver)

    return assembly


# ── Main: build and export when run directly ──────────────────────

if __name__ == "__main__":
    import os

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("Building full collector assembly...")
    assembly = make_assembly()

    print("Exporting STEP...")
    cq.exporters.export(assembly, os.path.join(output_dir, "collector_assembly.step"))
    print("  → collector_assembly.step")

    print("Exporting STL...")
    cq.exporters.export(assembly, os.path.join(output_dir, "collector_assembly.stl"))
    print("  → collector_assembly.stl")

    print("Done.")
