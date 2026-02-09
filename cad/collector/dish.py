"""
Parabolic Dish Collector — CadQuery Parametric Model

Generates the 1 m parabolic dish with 8 petals, backup structure
(hub, radial ribs, rim ring), and flat petal patterns for fabrication.

All dimensions from docs/design/collector-design.md.
"""

import math
import cadquery as cq

# ── Design Parameters ──────────────────────────────────────────────

DISH_DIAMETER = 1000.0  # mm (1.0 m)
DISH_RADIUS = DISH_DIAMETER / 2.0
FOCAL_LENGTH = 600.0  # mm (0.60 m)
DISH_DEPTH = 104.17  # mm — D² / (16f) = 1000² / (16*600)
NUM_PETALS = 8
MIRROR_THICKNESS = 0.5  # mm (MIRO-SUN sheet)
SUBSTRATE_THICKNESS = 1.5  # mm (steel substrate under mirror)
PETAL_THICKNESS = MIRROR_THICKNESS + SUBSTRATE_THICKNESS  # 2.0 mm total

# Backup structure
RIB_WIDTH = 25.0  # mm (square tube outer dimension)
RIB_WALL = 1.5  # mm (tube wall thickness)
HUB_DIAMETER = 80.0  # mm
HUB_HEIGHT = 30.0  # mm
RIM_RING_WIDTH = 20.0  # mm (ring cross-section width)
RIM_RING_THICKNESS = 3.0  # mm

# Resolution
NUM_RADIAL_PTS = 40  # points along the radial direction for paraboloid
NUM_ANGULAR_PTS = 20  # points per petal angular span


def paraboloid_z(r: float) -> float:
    """Z coordinate on paraboloid at radial distance r from axis."""
    return r**2 / (4.0 * FOCAL_LENGTH)


def make_petal_surface_points(petal_index: int = 0):
    """Generate a grid of (x, y, z) points on one petal of the paraboloid.

    Returns a list of lists (rows of points), suitable for CadQuery loft.
    """
    angle_start = petal_index * (2 * math.pi / NUM_PETALS)
    angle_end = angle_start + (2 * math.pi / NUM_PETALS)

    rows = []
    for i_r in range(1, NUM_RADIAL_PTS + 1):
        r = DISH_RADIUS * i_r / NUM_RADIAL_PTS
        z = paraboloid_z(r)
        row = []
        for i_a in range(NUM_ANGULAR_PTS + 1):
            theta = angle_start + (angle_end - angle_start) * i_a / NUM_ANGULAR_PTS
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            row.append((x, y, z))
        rows.append(row)
    return rows


def make_petal_shell(petal_index: int = 0) -> cq.Solid:
    """Create a single petal as a thickened shell by lofting radial sections.

    Uses a series of wires at increasing radii, lofted together, then
    thickened with a shell operation.
    """
    angle_start = petal_index * (2 * math.pi / NUM_PETALS)
    angle_end = angle_start + (2 * math.pi / NUM_PETALS)

    # Build cross-section wires at each radius
    wires = []
    for i_r in range(1, NUM_RADIAL_PTS + 1):
        r = DISH_RADIUS * i_r / NUM_RADIAL_PTS
        z = paraboloid_z(r)
        pts = []
        for i_a in range(NUM_ANGULAR_PTS + 1):
            theta = angle_start + (angle_end - angle_start) * i_a / NUM_ANGULAR_PTS
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            pts.append((x, y, z))
        wire = cq.Workplane("XY").spline(pts)
        wires.append(wire)

    # Loft through the wires to create the petal surface
    loft = wires[0]
    for w in wires[1:]:
        loft = loft.add(w)

    return loft


def make_petal_solid(petal_index: int = 0) -> cq.Workplane:
    """Create a single petal as a solid by sweeping arc profiles radially.

    Builds the petal as a series of arc segments at each radial station,
    lofted together to create a thin shell solid.
    """
    angle_start = petal_index * (2 * math.pi / NUM_PETALS)
    angle_span = 2 * math.pi / NUM_PETALS

    # Create inner and outer paraboloid surfaces and close them
    # Strategy: revolve a parabolic profile over the petal's angular span,
    # then subtract the inner volume to leave a thin shell.

    # Generate the parabolic profile in the XZ plane
    profile_pts = []
    for i in range(NUM_RADIAL_PTS + 1):
        r = DISH_RADIUS * i / NUM_RADIAL_PTS
        z = paraboloid_z(r)
        profile_pts.append((r, z))

    # Create outer surface by revolving parabolic profile
    outer_profile = cq.Workplane("XZ").spline(profile_pts)

    # Close the profile to make a solid of revolution
    first = profile_pts[0]
    last = profile_pts[-1]

    # Build a closed wire: parabola + closing lines
    wp = cq.Workplane("XZ")
    wp = wp.moveTo(first[0], first[1])
    wp = wp.spline(profile_pts[1:])
    wp = wp.lineTo(last[0], last[1] - PETAL_THICKNESS)

    # Inner parabolic profile (offset inward by thickness)
    inner_pts = []
    for i in range(NUM_RADIAL_PTS, -1, -1):
        r = DISH_RADIUS * i / NUM_RADIAL_PTS
        z = paraboloid_z(r) - PETAL_THICKNESS
        inner_pts.append((r, z))

    wp = wp.spline(inner_pts[1:])
    wp = wp.close()

    # Revolve over the petal's angular span
    angle_deg = math.degrees(angle_span)
    solid = wp.revolve(angle_deg, (0, 0, 0), (0, 1, 0))

    # Rotate to the petal's starting angle
    angle_start_deg = math.degrees(angle_start)
    if angle_start_deg != 0:
        solid = solid.rotate((0, 0, 0), (0, 0, 1), angle_start_deg)

    return solid


def make_dish() -> cq.Workplane:
    """Create the full dish as a single 360° revolved paraboloid shell.

    Individual petals share exact boundary faces, so boolean union fails.
    Instead, revolve the full parabolic profile 360° to make one solid.
    """
    profile_pts = []
    for i in range(NUM_RADIAL_PTS + 1):
        r = DISH_RADIUS * i / NUM_RADIAL_PTS
        z = paraboloid_z(r)
        profile_pts.append((r, z))

    first = profile_pts[0]
    last = profile_pts[-1]

    # Build closed cross-section: outer parabola, closing line, inner parabola
    wp = cq.Workplane("XZ")
    wp = wp.moveTo(first[0], first[1])
    wp = wp.spline(profile_pts[1:])
    wp = wp.lineTo(last[0], last[1] - PETAL_THICKNESS)

    inner_pts = []
    for i in range(NUM_RADIAL_PTS, -1, -1):
        r = DISH_RADIUS * i / NUM_RADIAL_PTS
        z = paraboloid_z(r) - PETAL_THICKNESS
        inner_pts.append((r, z))

    wp = wp.spline(inner_pts[1:])
    wp = wp.close()

    # Full 360° revolve around the Z axis (expressed as Y in XZ plane)
    dish = wp.revolve(360, (0, 0, 0), (0, 1, 0))
    return dish


def make_hub() -> cq.Workplane:
    """Central hub — hollow cylinder at the dish vertex."""
    outer = cq.Workplane("XY").circle(HUB_DIAMETER / 2).extrude(HUB_HEIGHT)
    inner = cq.Workplane("XY").circle(HUB_DIAMETER / 2 - RIB_WALL * 2).extrude(HUB_HEIGHT)
    return outer.cut(inner)


def make_rib(rib_index: int = 0) -> cq.Workplane:
    """Single radial rib from hub to rim, following the paraboloid profile.

    The rib is a square-tube cross-section swept along the parabolic curve.
    Simplified here as a straight-line approximation (hub edge to rim).
    """
    angle = rib_index * (2 * math.pi / NUM_PETALS) + (math.pi / NUM_PETALS)
    angle_deg = math.degrees(angle)

    r_start = HUB_DIAMETER / 2
    r_end = DISH_RADIUS - RIM_RING_WIDTH / 2

    z_start = paraboloid_z(r_start)
    z_end = paraboloid_z(r_end)

    # Length of the rib
    length = math.sqrt((r_end - r_start) ** 2 + (z_end - z_start) ** 2)

    # Angle of rib from horizontal
    rib_elevation = math.degrees(math.atan2(z_end - z_start, r_end - r_start))

    # Create rib as a hollow square tube along X, then position it
    outer = (
        cq.Workplane("YZ")
        .rect(RIB_WIDTH, RIB_WIDTH)
        .extrude(length)
    )
    inner = (
        cq.Workplane("YZ")
        .rect(RIB_WIDTH - 2 * RIB_WALL, RIB_WIDTH - 2 * RIB_WALL)
        .extrude(length)
    )
    rib = outer.cut(inner)

    # Position: move to hub edge, rotate to follow parabola slope
    rib = rib.translate((0, 0, -RIB_WIDTH / 2))  # center on Z
    rib = rib.rotate((0, 0, 0), (0, 1, 0), rib_elevation)
    rib = rib.translate((r_start, 0, z_start))
    rib = rib.rotate((0, 0, 0), (0, 0, 1), angle_deg)

    return rib


def make_rim_ring() -> cq.Workplane:
    """Rim ring at the dish perimeter — flat ring at rim height."""
    z_rim = paraboloid_z(DISH_RADIUS)
    outer = (
        cq.Workplane("XY")
        .workplane(offset=z_rim)
        .circle(DISH_RADIUS)
        .circle(DISH_RADIUS - RIM_RING_WIDTH)
        .extrude(RIM_RING_THICKNESS)
    )
    return outer


def make_backup_structure() -> cq.Workplane:
    """Complete backup structure: hub + 8 ribs + rim ring."""
    structure = make_hub()
    for i in range(NUM_PETALS):
        structure = structure.union(make_rib(i))
    structure = structure.union(make_rim_ring())
    return structure


def make_petal_flat_pattern(petal_index: int = 0) -> cq.Workplane:
    """Generate a flat (unfolded) 2D pattern for a single petal.

    Approximates the 3D petal surface as a flat gore by computing the
    arc lengths along the paraboloid and laying them out flat.
    The result is a 2D shape suitable for DXF export and laser cutting.
    """
    angle_span = 2 * math.pi / NUM_PETALS

    # Compute cumulative arc length along the parabolic meridian
    arc_lengths = [0.0]
    for i in range(1, NUM_RADIAL_PTS + 1):
        r_prev = DISH_RADIUS * (i - 1) / NUM_RADIAL_PTS
        r_curr = DISH_RADIUS * i / NUM_RADIAL_PTS
        z_prev = paraboloid_z(r_prev)
        z_curr = paraboloid_z(r_curr)
        ds = math.sqrt((r_curr - r_prev) ** 2 + (z_curr - z_prev) ** 2)
        arc_lengths.append(arc_lengths[-1] + ds)

    total_length = arc_lengths[-1]

    # For each radial station, compute the half-width at that station
    # Width = r * angle_span (circumferential arc), adjusted for surface slope
    right_edge = []
    left_edge = []

    for i in range(NUM_RADIAL_PTS + 1):
        r = DISH_RADIUS * i / NUM_RADIAL_PTS
        s = arc_lengths[i]  # distance from center along surface

        # Half-width at this radius
        half_w = r * angle_span / 2.0

        # Y coordinate is distance along the meridian (laid out vertically)
        right_edge.append((half_w, s))
        left_edge.append((-half_w, s))

    # Build the outline: up the right edge, down the left edge
    pts = [(0, 0)]  # vertex point
    pts.extend(right_edge[1:])  # skip duplicate origin
    pts.extend(reversed(left_edge[1:]))  # back down left side

    # Create a 2D wire and face
    flat = cq.Workplane("XY").polyline(pts).close().extrude(MIRROR_THICKNESS)

    return flat


def make_petal_flat_pattern_2d(petal_index: int = 0) -> cq.Workplane:
    """Generate a flat 2D petal pattern as a thin face (for DXF export).

    Returns a workplane with a 2D wire suitable for DXF export.
    """
    angle_span = 2 * math.pi / NUM_PETALS

    arc_lengths = [0.0]
    for i in range(1, NUM_RADIAL_PTS + 1):
        r_prev = DISH_RADIUS * (i - 1) / NUM_RADIAL_PTS
        r_curr = DISH_RADIUS * i / NUM_RADIAL_PTS
        z_prev = paraboloid_z(r_prev)
        z_curr = paraboloid_z(r_curr)
        ds = math.sqrt((r_curr - r_prev) ** 2 + (z_curr - z_prev) ** 2)
        arc_lengths.append(arc_lengths[-1] + ds)

    right_edge = []
    left_edge = []

    for i in range(NUM_RADIAL_PTS + 1):
        r = DISH_RADIUS * i / NUM_RADIAL_PTS
        s = arc_lengths[i]
        half_w = r * angle_span / 2.0
        right_edge.append((half_w, s))
        left_edge.append((-half_w, s))

    pts = [(0.0, 0.0)]
    pts.extend(right_edge[1:])
    pts.extend(reversed(left_edge[1:]))

    flat = cq.Workplane("XY").polyline(pts).close()
    return flat


# ── Main: build and export when run directly ──────────────────────

if __name__ == "__main__":
    import os

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("Building parabolic dish petals...")
    dish = make_dish()
    cq.exporters.export(dish, os.path.join(output_dir, "dish.step"))
    cq.exporters.export(dish, os.path.join(output_dir, "dish.stl"))
    print("  → dish.step, dish.stl")

    print("Building backup structure...")
    structure = make_backup_structure()
    cq.exporters.export(structure, os.path.join(output_dir, "backup_structure.step"))
    cq.exporters.export(structure, os.path.join(output_dir, "backup_structure.stl"))
    print("  → backup_structure.step, backup_structure.stl")

    print("Building flat petal pattern...")
    petal_flat = make_petal_flat_pattern(0)
    cq.exporters.export(petal_flat, os.path.join(output_dir, "petal_flat_pattern.step"))
    cq.exporters.export(petal_flat, os.path.join(output_dir, "petal_flat_pattern.stl"))
    print("  → petal_flat_pattern.step, petal_flat_pattern.stl")

    print("Exporting 2D flat pattern (DXF)...")
    petal_2d = make_petal_flat_pattern_2d(0)
    cq.exporters.export(petal_2d, os.path.join(output_dir, "petal_flat_pattern.dxf"))
    print("  → petal_flat_pattern.dxf")

    print("Done.")
