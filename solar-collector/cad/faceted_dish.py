"""
Faceted Dish — Hexagonal Flat Mirror Approximation

Approximates a parabolic dish with ~140 flat hexagonal mirrors (75 mm flat-to-flat),
each individually angled to reflect incoming sunlight toward the focal point.
Much easier to fabricate than a smooth paraboloid: buy flat mirrors, attach to an
angled frame.

All dimensions from docs/design/collector-design.md and efficiency-targets.md.
"""

import math
import cadquery as cq

# ── Design Parameters ──────────────────────────────────────────────

DISH_DIAMETER = 1000.0   # mm (1.0 m)
DISH_RADIUS = DISH_DIAMETER / 2.0
FOCAL_LENGTH = 600.0     # mm (same as smooth dish)
FACET_SIZE = 75.0        # mm (flat-to-flat hexagon dimension)
FACET_THICKNESS = 3.0    # mm (mirror glass thickness)
FRAME_TUBE_SIZE = 15.0   # mm (square tube for frame)
FRAME_TUBE_WALL = 1.5    # mm
MIRROR_GAP = 2.0         # mm (gap between mirrors for mounting tolerance)

# Backup structure (reuse hub/rim dimensions from dish.py)
HUB_DIAMETER = 80.0      # mm
HUB_HEIGHT = 30.0        # mm
RIM_RING_WIDTH = 20.0    # mm
RIM_RING_THICKNESS = 3.0 # mm
NUM_RIBS = 8


def paraboloid_z(x: float, y: float) -> float:
    """Z coordinate on paraboloid at position (x, y)."""
    return (x ** 2 + y ** 2) / (4.0 * FOCAL_LENGTH)


def hex_grid_positions(radius: float, facet_size: float, gap: float):
    """Generate hexagonal grid center positions within a circle of given radius.

    Uses axial coordinates for hex grid layout. Returns list of (x, y) tuples.
    The hex grid uses flat-top orientation with spacing = facet_size + gap.
    """
    spacing = facet_size + gap
    # Hex grid spacing: flat-top hexagons
    # Column spacing (horizontal) = spacing
    # Row spacing (vertical) = spacing * sqrt(3)/2
    col_spacing = spacing
    row_spacing = spacing * math.sqrt(3) / 2.0

    # Determine range of rows and columns needed
    max_cols = int(math.ceil(radius / col_spacing)) + 1
    max_rows = int(math.ceil(radius / row_spacing)) + 1

    positions = []
    for row in range(-max_rows, max_rows + 1):
        for col in range(-max_cols, max_cols + 1):
            x = col * col_spacing
            # Offset odd rows by half a column
            if row % 2 != 0:
                x += col_spacing / 2.0
            y = row * row_spacing

            # Check if this hex center is within the dish radius
            # Account for hex corners: inradius = facet_size/2
            dist = math.sqrt(x ** 2 + y ** 2)
            if dist + facet_size / 2.0 <= radius:
                positions.append((x, y))

    return positions


def facet_tilt_angles(x: float, y: float, focal_length: float):
    """Compute rotation angles to tilt a flat facet so it reflects vertical
    sunlight toward the focal point.

    Returns (tilt_x, tilt_y) rotation angles in degrees. The facet normal
    must bisect the angle between the incoming ray (0, 0, -1) and the
    reflected ray toward the focal point.
    """
    z = paraboloid_z(x, y)

    # The paraboloid surface normal at (x, y, z) points in direction:
    #   n = (-x/(2f), -y/(2f), 1), normalized
    # This is exactly the bisector we need for a flat mirror at this point.
    nx = -x / (2.0 * focal_length)
    ny = -y / (2.0 * focal_length)
    nz = 1.0
    n_len = math.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    nx /= n_len
    ny /= n_len
    nz /= n_len

    # Convert normal direction to tilt angles.
    # A flat facet starts with normal along +Z (0, 0, 1).
    # We need to rotate it so its normal aligns with (nx, ny, nz).
    #
    # Tilt around Y axis: angle = atan2(nx, nz)
    # Tilt around X axis: angle = -atan2(ny, nz)
    tilt_y = math.degrees(math.atan2(nx, nz))
    tilt_x = -math.degrees(math.atan2(ny, nz))

    return tilt_x, tilt_y


def _hex_wire(facet_size: float) -> cq.Workplane:
    """Create a flat-top regular hexagon wire on XY plane (centered at origin).

    facet_size is flat-to-flat dimension.
    """
    # Inradius (center to flat) = facet_size / 2
    # Circumradius (center to vertex) = facet_size / sqrt(3)
    circumradius = facet_size / math.sqrt(3)
    pts = []
    for i in range(6):
        angle = math.radians(60 * i + 30)  # pointy-top: vertex at 30°
        pts.append((circumradius * math.cos(angle), circumradius * math.sin(angle)))
    return cq.Workplane("XY").polyline(pts).close()


def make_facet(x: float, y: float) -> cq.Workplane:
    """Create a single hexagonal mirror facet, positioned and tilted on the paraboloid."""
    z = paraboloid_z(x, y)
    tilt_x, tilt_y = facet_tilt_angles(x, y, FOCAL_LENGTH)

    # Build hex prism at origin
    facet = _hex_wire(FACET_SIZE).extrude(FACET_THICKNESS)

    # Center thickness on Z=0
    facet = facet.translate((0, 0, -FACET_THICKNESS / 2.0))

    # Apply tilts (rotate around Y then X)
    facet = facet.rotate((0, 0, 0), (0, 1, 0), tilt_y)
    facet = facet.rotate((0, 0, 0), (1, 0, 0), tilt_x)

    # Translate to paraboloid position
    facet = facet.translate((x, y, z))

    return facet


def make_faceted_dish() -> cq.Assembly:
    """Create all hexagonal mirror facets as a cq.Assembly."""
    positions = hex_grid_positions(DISH_RADIUS, FACET_SIZE, MIRROR_GAP)
    print(f"  Facet count: {len(positions)}")

    assy = cq.Assembly(name="faceted_dish")
    for i, (x, y) in enumerate(positions):
        facet = make_facet(x, y)
        assy.add(facet, name=f"facet_{i}", color=cq.Color("lightgray"))

    return assy


def make_frame() -> cq.Workplane:
    """Support frame: hub + radial ribs + rim ring + mounting posts for each facet.

    Follows the same structural pattern as the existing backup structure in dish.py.
    """
    # ── Hub ────────────────────────────────────────────────────────
    hub_outer = cq.Workplane("XY").circle(HUB_DIAMETER / 2).extrude(HUB_HEIGHT)
    hub_inner = cq.Workplane("XY").circle(HUB_DIAMETER / 2 - FRAME_TUBE_WALL * 2).extrude(HUB_HEIGHT)
    frame = hub_outer.cut(hub_inner)

    # ── Radial ribs ────────────────────────────────────────────────
    for i in range(NUM_RIBS):
        angle = i * (360.0 / NUM_RIBS) + (180.0 / NUM_RIBS)
        angle_rad = math.radians(angle)

        r_start = HUB_DIAMETER / 2
        r_end = DISH_RADIUS - RIM_RING_WIDTH / 2
        z_start = paraboloid_z(r_start, 0)  # radial distance only
        z_end = paraboloid_z(r_end, 0)

        length = math.sqrt((r_end - r_start) ** 2 + (z_end - z_start) ** 2)
        rib_elevation = math.degrees(math.atan2(z_end - z_start, r_end - r_start))

        outer = cq.Workplane("YZ").rect(FRAME_TUBE_SIZE, FRAME_TUBE_SIZE).extrude(length)
        inner = (
            cq.Workplane("YZ")
            .rect(FRAME_TUBE_SIZE - 2 * FRAME_TUBE_WALL, FRAME_TUBE_SIZE - 2 * FRAME_TUBE_WALL)
            .extrude(length)
        )
        rib = outer.cut(inner)

        rib = rib.translate((0, 0, -FRAME_TUBE_SIZE / 2))
        rib = rib.rotate((0, 0, 0), (0, 1, 0), rib_elevation)
        rib = rib.translate((r_start, 0, z_start))
        rib = rib.rotate((0, 0, 0), (0, 0, 1), angle)

        frame = frame.union(rib)

    # ── Rim ring ──────────────────────────────────────────────────
    z_rim = paraboloid_z(DISH_RADIUS, 0)
    rim = (
        cq.Workplane("XY")
        .workplane(offset=z_rim)
        .circle(DISH_RADIUS)
        .circle(DISH_RADIUS - RIM_RING_WIDTH)
        .extrude(RIM_RING_THICKNESS)
    )
    frame = frame.union(rim)

    # ── Mounting posts for each facet ─────────────────────────────
    positions = hex_grid_positions(DISH_RADIUS, FACET_SIZE, MIRROR_GAP)
    for x, y in positions:
        r = math.sqrt(x ** 2 + y ** 2)
        if r < FRAME_TUBE_SIZE:
            # Skip posts at the very center (hub covers it)
            continue

        z_facet = paraboloid_z(x, y)

        # Post runs vertically from the base plane (z=0) up to facet z position
        # Minimum post height to avoid degenerate geometry
        post_height = max(z_facet, FRAME_TUBE_SIZE)

        post_outer = (
            cq.Workplane("XY")
            .rect(FRAME_TUBE_SIZE, FRAME_TUBE_SIZE)
            .extrude(post_height)
        )
        post_inner = (
            cq.Workplane("XY")
            .rect(FRAME_TUBE_SIZE - 2 * FRAME_TUBE_WALL, FRAME_TUBE_SIZE - 2 * FRAME_TUBE_WALL)
            .extrude(post_height)
        )
        post = post_outer.cut(post_inner)
        post = post.translate((x, y, 0))
        frame = frame.union(post)

    return frame


def make_faceted_assembly() -> cq.Assembly:
    """Complete faceted dish assembly: mirrors + support frame."""
    assy = cq.Assembly(name="faceted_assembly")

    print("  Building mirror facets...")
    facet_dish = make_faceted_dish()
    assy.add(facet_dish, name="mirrors")

    print("  Building support frame...")
    frame = make_frame()
    assy.add(frame, name="frame", color=cq.Color("steelblue"))

    return assy


# ── Main: build and export when run directly ──────────────────────

if __name__ == "__main__":
    import os

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("Building faceted dish (hexagonal mirrors)...")
    facet_dish = make_faceted_dish()
    path = os.path.join(output_dir, "faceted_dish.step")
    facet_dish.save(path)
    print(f"  → faceted_dish.step")

    print("Building support frame...")
    frame = make_frame()
    cq.exporters.export(frame, os.path.join(output_dir, "faceted_frame.step"))
    cq.exporters.export(frame, os.path.join(output_dir, "faceted_frame.stl"))
    print("  → faceted_frame.step, faceted_frame.stl")

    print("Building faceted assembly...")
    assy = make_faceted_assembly()
    path = os.path.join(output_dir, "faceted_assembly.step")
    assy.save(path)
    print(f"  → faceted_assembly.step")

    print("Done.")
