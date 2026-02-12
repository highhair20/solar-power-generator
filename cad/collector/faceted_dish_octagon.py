"""
Faceted Dish — Octagon + Square Tiling Variant

Approximates a parabolic dish using a truncated square tiling: large regular
octagonal mirrors with small square mirrors filling the interstices. This
achieves 100% fill (no gaps) with only two shape types. Larger octagonal facets
give better per-facet optical approximation than the hexagonal variant.

Each mirror is individually angled to reflect incoming sunlight toward the
focal point. All dimensions from docs/design/collector-design.md and
efficiency-targets.md.
"""

import math
import cadquery as cq

from faceted_dish import paraboloid_z, facet_tilt_angles

# ── Design Parameters ──────────────────────────────────────────────

DISH_DIAMETER = 1000.0   # mm (1.0 m)
DISH_RADIUS = DISH_DIAMETER / 2.0
FOCAL_LENGTH = 600.0     # mm (same as smooth dish)
OCTAGON_SIZE = 90.0      # mm (flat-to-flat octagon dimension)
FACET_THICKNESS = 3.0    # mm (mirror glass thickness)
FRAME_TUBE_SIZE = 15.0   # mm (square tube for frame)
FRAME_TUBE_WALL = 1.5    # mm
MIRROR_GAP = 2.0         # mm (gap between mirrors for mounting tolerance)

# Derived geometry
# In a truncated square tiling, the octagon edge length equals the square side
OCTAGON_EDGE = OCTAGON_SIZE * (math.sqrt(2) - 1)
SQUARE_SIZE = OCTAGON_EDGE  # side length of the interstitial squares

# Center-to-center spacing between adjacent octagons along grid axes
GRID_SPACING = OCTAGON_SIZE * math.sqrt(2) + MIRROR_GAP

# Backup structure
HUB_DIAMETER = 80.0      # mm
HUB_HEIGHT = 30.0        # mm
RIM_RING_WIDTH = 20.0    # mm
RIM_RING_THICKNESS = 3.0 # mm
NUM_RIBS = 8


def octagon_square_grid(radius, octagon_size, gap):
    """Generate center positions for octagon and square mirrors within a circle.

    Uses a truncated square tiling layout. Returns (oct_positions, sq_positions)
    as lists of (x, y) tuples.
    """
    spacing = octagon_size * math.sqrt(2) + gap
    max_n = int(math.ceil(radius / spacing)) + 1

    oct_positions = []
    sq_positions = []

    # Octagons on a square grid
    for row in range(-max_n, max_n + 1):
        for col in range(-max_n, max_n + 1):
            x = col * spacing
            y = row * spacing
            dist = math.sqrt(x ** 2 + y ** 2)
            if dist + octagon_size / 2.0 <= radius:
                oct_positions.append((x, y))

    # Squares at the centers between four octagon neighbors (offset by half spacing)
    sq_edge = octagon_size * (math.sqrt(2) - 1)
    for row in range(-max_n, max_n + 1):
        for col in range(-max_n, max_n + 1):
            x = (col + 0.5) * spacing
            y = (row + 0.5) * spacing
            dist = math.sqrt(x ** 2 + y ** 2)
            # Square inscribed radius = side / sqrt(2) (rotated 45°)
            if dist + sq_edge / math.sqrt(2) <= radius:
                sq_positions.append((x, y))

    return oct_positions, sq_positions


def _octagon_wire(size):
    """Create a regular octagon wire on XY plane (centered at origin).

    size is flat-to-flat dimension.
    """
    # Circumradius (center to vertex) for a regular octagon
    # inradius = size / 2, circumradius = inradius / cos(pi/8)
    circumradius = (size / 2.0) / math.cos(math.pi / 8)
    pts = []
    for i in range(8):
        # Start with a flat edge on top: offset by half a segment (pi/8)
        angle = math.pi / 8 + i * (math.pi / 4)
        pts.append((circumradius * math.cos(angle), circumradius * math.sin(angle)))
    return cq.Workplane("XY").polyline(pts).close()


def _square_wire(size):
    """Create a square wire on XY plane, rotated 45° (diamond orientation).

    size is the side length.
    """
    # A square rotated 45° has vertices at distance side/sqrt(2) from center
    half_diag = size / math.sqrt(2)
    pts = [
        (half_diag, 0),
        (0, half_diag),
        (-half_diag, 0),
        (0, -half_diag),
    ]
    return cq.Workplane("XY").polyline(pts).close()


def make_octagon_facet(x, y):
    """Create a single octagonal mirror facet, positioned and tilted on the paraboloid."""
    z = paraboloid_z(x, y)
    tilt_x, tilt_y = facet_tilt_angles(x, y, FOCAL_LENGTH)

    facet = _octagon_wire(OCTAGON_SIZE).extrude(FACET_THICKNESS)
    facet = facet.translate((0, 0, -FACET_THICKNESS / 2.0))

    facet = facet.rotate((0, 0, 0), (0, 1, 0), tilt_y)
    facet = facet.rotate((0, 0, 0), (1, 0, 0), tilt_x)
    facet = facet.translate((x, y, z))

    return facet


def make_square_facet(x, y):
    """Create a single square mirror facet (45° rotated), positioned and tilted."""
    z = paraboloid_z(x, y)
    tilt_x, tilt_y = facet_tilt_angles(x, y, FOCAL_LENGTH)

    facet = _square_wire(SQUARE_SIZE).extrude(FACET_THICKNESS)
    facet = facet.translate((0, 0, -FACET_THICKNESS / 2.0))

    facet = facet.rotate((0, 0, 0), (0, 1, 0), tilt_y)
    facet = facet.rotate((0, 0, 0), (1, 0, 0), tilt_x)
    facet = facet.translate((x, y, z))

    return facet


def make_faceted_dish_octagon():
    """Create all octagonal and square mirror facets as a cq.Assembly."""
    oct_positions, sq_positions = octagon_square_grid(
        DISH_RADIUS, OCTAGON_SIZE, MIRROR_GAP
    )
    print(f"  Octagon facets: {len(oct_positions)}")
    print(f"  Square facets:  {len(sq_positions)}")
    print(f"  Total facets:   {len(oct_positions) + len(sq_positions)}")

    assy = cq.Assembly(name="octagon_dish")

    for i, (x, y) in enumerate(oct_positions):
        facet = make_octagon_facet(x, y)
        assy.add(facet, name=f"oct_{i}", color=cq.Color("lightgray"))

    for i, (x, y) in enumerate(sq_positions):
        facet = make_square_facet(x, y)
        assy.add(facet, name=f"sq_{i}", color=cq.Color("lightyellow"))

    return assy


def make_frame():
    """Support frame: hub + radial ribs + rim ring + mounting posts for each facet.

    Follows the same structural pattern as faceted_dish.py.
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
        z_start = paraboloid_z(r_start, 0)
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
    oct_positions, sq_positions = octagon_square_grid(
        DISH_RADIUS, OCTAGON_SIZE, MIRROR_GAP
    )
    all_positions = oct_positions + sq_positions
    for x, y in all_positions:
        r = math.sqrt(x ** 2 + y ** 2)
        if r < FRAME_TUBE_SIZE:
            continue

        z_facet = paraboloid_z(x, y)
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


def make_faceted_assembly_octagon():
    """Complete octagon+square faceted dish assembly: mirrors + support frame."""
    assy = cq.Assembly(name="octagon_assembly")

    print("  Building octagon+square mirror facets...")
    facet_dish = make_faceted_dish_octagon()
    assy.add(facet_dish, name="mirrors")

    print("  Building support frame...")
    frame_solid = make_frame()
    assy.add(frame_solid, name="frame", color=cq.Color("steelblue"))

    return assy


# ── Main: build and export when run directly ──────────────────────

if __name__ == "__main__":
    import os

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("Building faceted dish (octagon+square mirrors)...")
    facet_dish = make_faceted_dish_octagon()
    path = os.path.join(output_dir, "octagon_dish.step")
    facet_dish.save(path)
    print(f"  → octagon_dish.step")

    print("Building support frame...")
    frame = make_frame()
    cq.exporters.export(frame, os.path.join(output_dir, "octagon_frame.step"))
    cq.exporters.export(frame, os.path.join(output_dir, "octagon_frame.stl"))
    print("  → octagon_frame.step, octagon_frame.stl")

    print("Building octagon+square assembly...")
    assy = make_faceted_assembly_octagon()
    path = os.path.join(output_dir, "octagon_assembly.step")
    assy.save(path)
    print(f"  → octagon_assembly.step")

    print("Done.")
