"""
Free-Piston Stirling Engine — CadQuery Parametric Model

Generates a conceptual/dimensional model of a free-piston Stirling engine
with linear alternator (Infinia/Qnergy style). No crankshaft — the displacer
and power piston oscillate freely inside a sealed pressure vessel.

Sized for ~200W electrical output from ~550W thermal input (1m dish).
Pressurized helium working gas.

Uses magnetic springs (opposing permanent magnet rings) instead of
mechanical flexure springs for displacer resonance — no fatigue failure,
non-contact, longer life.

Includes a half-section cutaway to reveal internal components.
"""

import math
import cadquery as cq

# ── Design Parameters ──────────────────────────────────────────────

# Pressure vessel
VESSEL_OD = 100.0       # mm — outer diameter
VESSEL_WALL = 5.0       # mm — pressure-rated wall thickness
VESSEL_ID = VESSEL_OD - 2 * VESSEL_WALL  # 90 mm
VESSEL_LENGTH = 250.0   # mm — total length (excluding heater head)

# Heater head (hot end)
HEATER_HEAD_OD = 80.0       # mm — slightly smaller than vessel
HEATER_HEAD_LENGTH = 40.0   # mm — cylindrical head
HEATER_HEAD_WALL = 4.0      # mm — thick for heat transfer + pressure
HEATER_FIN_COUNT = 8        # external radial fins
HEATER_FIN_HEIGHT = 20.0    # mm
HEATER_FIN_THICKNESS = 2.0  # mm

# Displacer
DISPLACER_OD = VESSEL_ID - 4.0   # mm — clearance seal
DISPLACER_LENGTH = 50.0          # mm
DISPLACER_WALL = 1.5             # mm — lightweight
DISPLACER_ROD_DIA = 8.0          # mm

# Magnetic spring (opposing permanent magnet rings)
MAG_SPRING_OD = VESSEL_ID - 4.0    # mm — fits inside vessel with clearance
MAG_SPRING_ID = DISPLACER_ROD_DIA + 6.0  # mm — clears displacer rod
MAG_SPRING_LENGTH = 8.0           # mm — axial thickness of each magnet ring
MAG_SPRING_GAP = 10.0             # mm — nominal gap between opposing rings
MAG_SPRING_HOUSING_WALL = 2.0     # mm — retainer ring wall thickness

# Power piston
PISTON_OD = 70.0         # mm
PISTON_LENGTH = 25.0     # mm
PISTON_WALL = 8.0        # mm — heavier for inertia

# Linear alternator
MAGNET_RING_OD = VESSEL_ID - 2.0  # mm — fits inside vessel
MAGNET_RING_ID = MAGNET_RING_OD - 15.0  # mm — magnet thickness ~7.5mm
MAGNET_RING_LENGTH = 30.0  # mm
STATOR_OD = VESSEL_OD + 20.0  # mm — wraps around vessel exterior
STATOR_ID = VESSEL_OD - 1.0   # mm — small gap to vessel wall
STATOR_LENGTH = 40.0          # mm

# Cooler
COOLER_FIN_COUNT = 20
COOLER_FIN_HEIGHT = 15.0  # mm
COOLER_FIN_THICKNESS = 1.0  # mm
COOLER_ZONE_LENGTH = 30.0  # mm — axial length of cooled region

# Bounce space (gas spring behind power piston)
BOUNCE_SPACE_LENGTH = 40.0  # mm

# Internal layout positions (Z axis, 0 = bottom of vessel)
Z_BOUNCE_END = 0.0
Z_PISTON = BOUNCE_SPACE_LENGTH
Z_ALTERNATOR = Z_PISTON + PISTON_LENGTH + 10
Z_MAG_FIXED = Z_ALTERNATOR + MAGNET_RING_LENGTH + 15  # fixed magnet ring (vessel-mounted)
Z_MAG_MOVING = Z_MAG_FIXED + MAG_SPRING_LENGTH + MAG_SPRING_GAP  # moving magnet ring (displacer-mounted)
Z_DISPLACER = Z_MAG_MOVING + MAG_SPRING_LENGTH + 10
Z_HEATER = VESSEL_LENGTH


# ── Component Functions ────────────────────────────────────────────

def make_pressure_vessel() -> cq.Workplane:
    """Main cylindrical pressure vessel — sealed housing for all internals.

    Axis along Z. Closed at both ends. Top has a bore for the heater head
    to insert into (sealed with a shoulder).
    """
    # Outer shell
    outer = cq.Workplane("XY").circle(VESSEL_OD / 2).extrude(VESSEL_LENGTH)

    # Inner bore — stops short of the top, leaving a top wall
    inner = (
        cq.Workplane("XY")
        .workplane(offset=VESSEL_WALL)
        .circle(VESSEL_ID / 2)
        .extrude(VESSEL_LENGTH - 2 * VESSEL_WALL)
    )
    vessel = outer.cut(inner)

    # Heater head bore — hole through the top wall for the heater head to insert
    heater_bore = (
        cq.Workplane("XY")
        .workplane(offset=VESSEL_LENGTH - VESSEL_WALL)
        .circle(HEATER_HEAD_OD / 2)
        .extrude(VESSEL_WALL)
    )
    vessel = vessel.cut(heater_bore)

    return vessel


def make_heater_head() -> cq.Workplane:
    """Hot-end heater head — receives concentrated solar heat.

    Sits on top of the pressure vessel. Has external fins for
    heat absorption from the receiver cavity.
    """
    od = HEATER_HEAD_OD
    wall = HEATER_HEAD_WALL
    length = HEATER_HEAD_LENGTH

    # Main head body — cup shape (closed at top, open at bottom)
    outer = cq.Workplane("XY").circle(od / 2).extrude(length)
    inner = (
        cq.Workplane("XY")
        .circle(od / 2 - wall)
        .extrude(length - wall)
    )
    head = outer.cut(inner)

    # External heat-absorbing fins — radial plates
    for i in range(HEATER_FIN_COUNT):
        angle = i * (360.0 / HEATER_FIN_COUNT)
        angle_rad = math.radians(angle)

        # Fin plate extending radially outward
        r_mid = od / 2 + HEATER_FIN_HEIGHT / 2
        cx = r_mid * math.cos(angle_rad)
        cy = r_mid * math.sin(angle_rad)

        fin = (
            cq.Workplane("XY")
            .center(cx, cy)
            .rect(HEATER_FIN_HEIGHT, HEATER_FIN_THICKNESS)
            .extrude(length * 0.8)
        )
        # Rotate the fin to be radial
        fin = fin.rotate((0, 0, 0), (0, 0, 1), angle)
        head = head.union(fin)

    return head


def make_displacer() -> cq.Workplane:
    """Free-floating displacer — lightweight hollow cylinder with rod.

    Oscillates in the hot space driven by pressure differential.
    """
    # Hollow cylinder
    outer = cq.Workplane("XY").circle(DISPLACER_OD / 2).extrude(DISPLACER_LENGTH)
    inner = (
        cq.Workplane("XY")
        .circle(DISPLACER_OD / 2 - DISPLACER_WALL)
        .extrude(DISPLACER_LENGTH)
    )
    displacer = outer.cut(inner)

    # End caps
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

    # Displacer rod extending downward (toward power piston)
    rod_length = Z_DISPLACER - Z_MAG_FIXED - 10
    rod = (
        cq.Workplane("XY")
        .workplane(offset=-DISPLACER_WALL)
        .circle(DISPLACER_ROD_DIA / 2)
        .extrude(-rod_length)
    )
    displacer = displacer.union(rod)

    return displacer


def make_magnetic_spring_fixed() -> cq.Workplane:
    """Fixed magnet ring — mounted to pressure vessel wall.

    NdFeB ring magnet with a retainer housing. Polarized axially
    to repel the moving ring on the displacer rod.
    """
    # Retainer housing (non-magnetic, e.g. aluminum or stainless)
    housing = (
        cq.Workplane("XY")
        .circle(MAG_SPRING_OD / 2 + MAG_SPRING_HOUSING_WALL)
        .circle(MAG_SPRING_ID / 2 - MAG_SPRING_HOUSING_WALL)
        .extrude(MAG_SPRING_LENGTH)
    )

    # Magnet ring (inset into housing)
    magnet = (
        cq.Workplane("XY")
        .circle(MAG_SPRING_OD / 2)
        .circle(MAG_SPRING_ID / 2)
        .extrude(MAG_SPRING_LENGTH)
    )

    return housing.union(magnet)


def make_magnetic_spring_moving() -> cq.Workplane:
    """Moving magnet ring — attached to displacer rod.

    Polarized to repel the fixed ring. Rides on the displacer rod
    and oscillates with it, providing the restoring force.
    """
    # Magnet ring
    magnet = (
        cq.Workplane("XY")
        .circle(MAG_SPRING_OD / 2)
        .circle(MAG_SPRING_ID / 2)
        .extrude(MAG_SPRING_LENGTH)
    )

    # Hub connecting magnet to displacer rod
    hub = (
        cq.Workplane("XY")
        .circle(MAG_SPRING_ID / 2)
        .circle(DISPLACER_ROD_DIA / 2)
        .extrude(MAG_SPRING_LENGTH)
    )

    return magnet.union(hub)


def make_power_piston() -> cq.Workplane:
    """Free-floating power piston with magnet ring for linear alternator.

    Heavier than displacer — provides inertial mass for the oscillating system.
    """
    # Main piston body
    piston = cq.Workplane("XY").circle(PISTON_OD / 2).extrude(PISTON_LENGTH)

    # Magnet ring — attached to the piston, extends into alternator region
    magnet = (
        cq.Workplane("XY")
        .workplane(offset=PISTON_LENGTH)
        .circle(MAGNET_RING_OD / 2)
        .circle(MAGNET_RING_ID / 2)
        .extrude(MAGNET_RING_LENGTH)
    )
    piston = piston.union(magnet)

    return piston


def make_alternator_stator() -> cq.Workplane:
    """Stator coil housing — wraps around the pressure vessel exterior.

    The magnet ring on the piston oscillates past the stator coils
    to generate electricity.
    """
    stator = (
        cq.Workplane("XY")
        .circle(STATOR_OD / 2)
        .circle(STATOR_ID / 2)
        .extrude(STATOR_LENGTH)
    )
    return stator


def make_cooler() -> cq.Workplane:
    """Cold-end cooler — external fins on the pressure vessel for heat rejection.

    Positioned between the alternator and the displacer space.
    """
    vessel_section_od = VESSEL_OD

    # Annular fin rings
    cooler = cq.Workplane("XY")  # placeholder
    fins = []
    for i in range(int(COOLER_ZONE_LENGTH / (COOLER_FIN_THICKNESS + 2))):
        z = i * (COOLER_FIN_THICKNESS + 2)
        fin = (
            cq.Workplane("XY")
            .workplane(offset=z)
            .circle(vessel_section_od / 2 + COOLER_FIN_HEIGHT)
            .circle(vessel_section_od / 2)
            .extrude(COOLER_FIN_THICKNESS)
        )
        fins.append(fin)

    if fins:
        cooler = fins[0]
        for f in fins[1:]:
            cooler = cooler.union(f)

    return cooler


def make_half_section_cut() -> cq.Workplane:
    """A large box used to cut the assembly in half for cross-section view."""
    cut_box = (
        cq.Workplane("XY")
        .workplane(offset=-50)
        .center(0, VESSEL_OD)
        .rect(VESSEL_OD * 3, VESSEL_OD * 2)
        .extrude(VESSEL_LENGTH + HEATER_HEAD_LENGTH + 100)
    )
    return cut_box


def make_free_piston_stirling() -> cq.Assembly:
    """Full free-piston Stirling engine assembly.

    Layout (Z axis, bottom to top):
    - Bounce space (sealed gas spring)
    - Power piston + magnet ring
    - Alternator stator (external)
    - Magnetic spring (fixed ring, vessel-mounted)
    - Magnetic spring (moving ring, displacer-mounted)
    - Displacer
    - Cooler fins (external)
    - Heater head
    """
    assy = cq.Assembly(name="free_piston_stirling")

    print("  Building pressure vessel...")
    vessel = make_pressure_vessel()
    assy.add(vessel, name="pressure_vessel", color=cq.Color("gray60"))

    print("  Building heater head...")
    heater = make_heater_head()
    heater = heater.translate((0, 0, VESSEL_LENGTH))
    assy.add(heater, name="heater_head", color=cq.Color("firebrick"))

    print("  Building displacer...")
    displacer = make_displacer()
    displacer = displacer.translate((0, 0, Z_DISPLACER))
    assy.add(displacer, name="displacer", color=cq.Color("orange"))

    print("  Building magnetic spring (fixed ring)...")
    mag_fixed = make_magnetic_spring_fixed()
    mag_fixed = mag_fixed.translate((0, 0, Z_MAG_FIXED))
    assy.add(mag_fixed, name="mag_spring_fixed", color=cq.Color("red3"))

    print("  Building magnetic spring (moving ring)...")
    mag_moving = make_magnetic_spring_moving()
    mag_moving = mag_moving.translate((0, 0, Z_MAG_MOVING))
    assy.add(mag_moving, name="mag_spring_moving", color=cq.Color("red1"))

    print("  Building power piston + magnets...")
    piston = make_power_piston()
    piston = piston.translate((0, 0, Z_PISTON))
    assy.add(piston, name="power_piston", color=cq.Color("goldenrod"))

    print("  Building alternator stator...")
    stator = make_alternator_stator()
    stator = stator.translate((0, 0, Z_ALTERNATOR))
    assy.add(stator, name="alternator_stator", color=cq.Color("darkgreen"))

    print("  Building cooler fins...")
    cooler = make_cooler()
    # Position cooler around the vessel between spring and heater
    cooler_z = Z_MAG_MOVING + MAG_SPRING_LENGTH + 5
    cooler = cooler.translate((0, 0, cooler_z))
    assy.add(cooler, name="cooler", color=cq.Color("steelblue"))

    return assy


# ── Main: build and export when run directly ──────────────────────

if __name__ == "__main__":
    import os

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("Building free-piston Stirling engine...")
    assembly = make_free_piston_stirling()

    print("Exporting STEP...")
    assembly.save(os.path.join(output_dir, "free_piston_stirling.step"))
    print("  → free_piston_stirling.step")

    # Export individual components for visualization
    print("Exporting individual STLs...")
    cq.exporters.export(make_pressure_vessel(), os.path.join(output_dir, "fp_pressure_vessel.stl"))
    cq.exporters.export(make_heater_head(), os.path.join(output_dir, "fp_heater_head.stl"))
    print("  → fp_pressure_vessel.stl, fp_heater_head.stl")

    print("Done.")
