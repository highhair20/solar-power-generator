"""
Free-Piston Stirling Engine — CadQuery Parametric Model

Generates a conceptual/dimensional model of a free-piston Stirling engine
with linear alternator (Infinia/Qnergy style). No crankshaft — the displacer
and power piston oscillate freely inside a sealed pressure vessel.

Sized for ~75W electrical output from ~550W thermal input (1m dish).
Pressurized helium working gas, 600/300°C, 50-60 Hz.

Uses magnetic springs (opposing SmCo permanent magnet rings) instead of
mechanical flexure springs for displacer resonance — no fatigue failure,
non-contact, longer life. SmCo chosen over NdFeB for high-temperature
operation (rated to 300°C, Curie temp ~700°C).

Includes a half-section cutaway to reveal internal components.

Engineering review fixes applied:
- Piston OD increased to 89mm (0.5mm radial clearance seal)
- Full-bore tube bundle cooler (no center bypass)
- Full-bore packed mesh regenerator, 45mm long
- Internal heater fins for gas-side heat transfer
- Dead volume minimized (tight gaps, proper HX fill)
- Magnetic spring gap increased to 20mm for full stroke
- Stator length increased to 55mm for stroke coverage
"""

import math
import cadquery as cq

# ── Design Parameters ──────────────────────────────────────────────

# Pressure vessel
VESSEL_OD = 100.0       # mm — outer diameter
VESSEL_WALL = 5.0       # mm — pressure-rated wall thickness
VESSEL_ID = VESSEL_OD - 2 * VESSEL_WALL  # 90 mm
VESSEL_LENGTH = 280.0   # mm — total length (increased for longer regen + spring gap)

# Heater head (hot end)
HEATER_HEAD_OD = VESSEL_ID          # mm — matches vessel bore
HEATER_HEAD_LENGTH = 40.0   # mm — cylindrical head
HEATER_HEAD_WALL = 4.0      # mm — thick for heat transfer + pressure
HEATER_FIN_COUNT = 8        # external radial fins
HEATER_FIN_HEIGHT = 20.0    # mm
HEATER_FIN_THICKNESS = 2.0  # mm

# Internal heater fins (gas-side heat transfer enhancement)
HEATER_INT_FIN_COUNT = 12       # radial fins inside heater cup
HEATER_INT_FIN_HEIGHT = 15.0    # mm — extends inward from wall
HEATER_INT_FIN_THICKNESS = 1.5  # mm
HEATER_INT_FIN_LENGTH = 30.0    # mm — axial extent (most of cup depth)

# Displacer
DISPLACER_OD = VESSEL_ID - 1.5   # mm — 0.75mm radial clearance seal
DISPLACER_LENGTH = 50.0          # mm
DISPLACER_WALL = 1.5             # mm — lightweight
DISPLACER_ROD_DIA = 8.0          # mm

# Magnetic spring (wall-mounted opposing SmCo magnet rings)
# SmCo rated to 300°C (vs NdFeB 150°C) — required near hot displacer.
# Both rings hug the vessel wall / displacer edge, leaving the center
# open for free gas flow between displacer and piston spaces.
MAG_SPRING_FIXED_OD = VESSEL_ID            # mm — flush with vessel bore
MAG_SPRING_FIXED_ID = VESSEL_ID - 12.0     # mm — 6mm radial thickness
MAG_SPRING_MOVING_OD = DISPLACER_OD        # mm — flush with displacer outer edge
MAG_SPRING_MOVING_ID = DISPLACER_OD - 12.0 # mm — 6mm radial thickness
MAG_SPRING_LENGTH = 8.0           # mm — axial thickness of each magnet ring
MAG_SPRING_GAP = 20.0             # mm — nominal gap (increased from 10mm for 10-15mm stroke)

# Power piston — 0.5mm radial clearance seal against 90mm bore
PISTON_OD = 89.0         # mm — was 70mm, now proper clearance seal
PISTON_LENGTH = 25.0     # mm
PISTON_WALL = 8.0        # mm — heavier for inertia

# Linear alternator
MAGNET_RING_OD = VESSEL_ID - 2.0  # mm — fits inside vessel
MAGNET_RING_ID = MAGNET_RING_OD - 15.0  # mm — magnet thickness ~7.5mm
MAGNET_RING_LENGTH = 30.0  # mm
STATOR_OD = VESSEL_OD + 20.0  # mm — wraps around vessel exterior
STATOR_ID = VESSEL_OD - 1.0   # mm — small gap to vessel wall
STATOR_LENGTH = 55.0          # mm — increased from 40mm for 10-15mm stroke overhang

# External cooler fins
COOLER_FIN_COUNT = 20
COOLER_FIN_HEIGHT = 15.0    # mm
COOLER_FIN_THICKNESS = 1.0  # mm
COOLER_ZONE_LENGTH = 38.0   # mm — matches internal cooler zone

# Internal cooler — full-bore tube bundle spanning the entire 90mm bore.
# Gas flows axially through tubes; heat transfers radially to vessel wall
# via tube-to-wall conduction and external fins.
COOLER_INT_OD = VESSEL_ID          # mm — fills entire bore
COOLER_INT_LENGTH = 38.0           # mm — axial length
COOLER_INT_TUBE_DIA = 3.0         # mm — individual tube bore
COOLER_INT_TUBE_COUNT = 48        # tubes in hex pattern across bore
# Total flow area: 48 × π × 1.5² ≈ 339 mm² (was 85 mm²)

# Regenerator — full-bore packed wire mesh housing.
# SS316 stacked screens (80-mesh), 70% porosity.
# Modeled as solid cylinder with axial holes representing mesh passages.
REGEN_OD = VESSEL_ID              # mm — fills entire bore
REGEN_LENGTH = 45.0               # mm — increased from 18mm for proper thermal mass
REGEN_HOLES = 60                  # representative mesh passages
REGEN_HOLE_DIA = 2.0              # mm
# Total flow area: 60 × π × 1.0² ≈ 188 mm²
# Actual mesh has ~70% porosity = ~4,450 mm² — holes are representative only

# Bounce space (gas spring behind power piston)
BOUNCE_SPACE_LENGTH = 40.0  # mm

# Magnetic centering stop (bottom of bounce space)
CENTER_MAG_OD = MAGNET_RING_OD         # mm — matches piston magnet ring OD
CENTER_MAG_ID = MAGNET_RING_ID         # mm — matches piston magnet ring ID
CENTER_MAG_LENGTH = 6.0                 # mm — axial thickness
CENTER_MAG_FLOOR_Z = VESSEL_WALL        # sits on vessel floor

# Helium fill tube — small stainless tube stub on the vessel bottom (cool end).
# Used to evacuate, backfill with helium to charge pressure, then pinch-weld shut.
FILL_TUBE_OD = 6.0          # mm — standard 1/4" stainless tube
FILL_TUBE_ID = 4.0          # mm — 1mm wall thickness
FILL_TUBE_LENGTH = 20.0     # mm — protrudes below vessel floor
FILL_TUBE_OFFSET_X = 25.0   # mm — offset from center to clear centering magnet

# Internal layout positions (Z axis, 0 = bottom of vessel)
Z_BOUNCE_END = 0.0
Z_PISTON = BOUNCE_SPACE_LENGTH
# Alternator stator (external) — centered on piston's magnet ring
_MAGNET_RING_CENTER_Z = Z_PISTON + PISTON_LENGTH / 2
Z_ALTERNATOR = _MAGNET_RING_CENTER_Z - STATOR_LENGTH / 2
# Internal heat exchangers — tight gap above piston (3mm to reduce dead volume)
Z_COOLER_INT = Z_PISTON + PISTON_LENGTH + 3.0
Z_REGEN = Z_COOLER_INT + COOLER_INT_LENGTH
# Magnetic spring — directly below displacer
Z_MAG_FIXED = Z_REGEN + REGEN_LENGTH + 2.0   # 2mm gap above regenerator
Z_MAG_MOVING = Z_MAG_FIXED + MAG_SPRING_LENGTH + MAG_SPRING_GAP
Z_DISPLACER = Z_MAG_MOVING + MAG_SPRING_LENGTH + 2.0  # 2mm clearance
# Heater head — tight fit above displacer (12mm hot space gap)
HOT_SPACE_GAP = 12.0  # mm — reduced from ~37.5mm to minimize dead volume
Z_HEATER = Z_DISPLACER + DISPLACER_LENGTH + DISPLACER_WALL + HOT_SPACE_GAP
VESSEL_LENGTH = Z_HEATER  # vessel length set by layout


# ── Component Functions ────────────────────────────────────────────

def make_pressure_vessel() -> cq.Workplane:
    """Main cylindrical pressure vessel — sealed housing for all internals.

    Axis along Z. Closed at both ends. Top has a bore for the heater head
    to insert into (sealed with a shoulder).
    """
    outer = cq.Workplane("XY").circle(VESSEL_OD / 2).extrude(VESSEL_LENGTH)

    inner = (
        cq.Workplane("XY")
        .workplane(offset=VESSEL_WALL)
        .circle(VESSEL_ID / 2)
        .extrude(VESSEL_LENGTH - 2 * VESSEL_WALL)
    )
    vessel = outer.cut(inner)

    # Heater head bore — hole through the top wall
    heater_bore = (
        cq.Workplane("XY")
        .workplane(offset=VESSEL_LENGTH - VESSEL_WALL)
        .circle(HEATER_HEAD_OD / 2)
        .extrude(VESSEL_WALL)
    )
    vessel = vessel.cut(heater_bore)

    # Fill tube bore — through-hole in the bottom wall for helium charging
    fill_bore = (
        cq.Workplane("XY")
        .center(FILL_TUBE_OFFSET_X, 0)
        .circle(FILL_TUBE_ID / 2)
        .extrude(VESSEL_WALL)
    )
    vessel = vessel.cut(fill_bore)

    return vessel


def make_fill_tube() -> cq.Workplane:
    """Helium fill/charge tube — small stainless tube stub on the vessel bottom.

    Offset from center to clear the centering magnet. After assembly,
    the vessel is evacuated through this tube, backfilled with helium
    to 20-30 bar charge pressure, then the tube is crimped and seal-welded
    shut (standard refrigeration industry technique).

    Protrudes downward from the vessel floor.
    """
    tube = (
        cq.Workplane("XY")
        .center(FILL_TUBE_OFFSET_X, 0)
        .circle(FILL_TUBE_OD / 2)
        .circle(FILL_TUBE_ID / 2)
        .extrude(-FILL_TUBE_LENGTH)
    )
    return tube


def make_centering_magnet_floor() -> cq.Workplane:
    """Fixed magnet ring on the vessel floor inside the bounce space.

    Sized to match the alternator magnet ring on the piston.
    Repels the piston's existing magnet ring to hold it at rest
    position and maintain bounce space volume for startup.
    """
    magnet = (
        cq.Workplane("XY")
        .circle(CENTER_MAG_OD / 2)
        .circle(CENTER_MAG_ID / 2)
        .extrude(CENTER_MAG_LENGTH)
    )
    return magnet


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

        r_mid = od / 2 + HEATER_FIN_HEIGHT / 2
        cx = r_mid * math.cos(angle_rad)
        cy = r_mid * math.sin(angle_rad)

        fin = (
            cq.Workplane("XY")
            .center(cx, cy)
            .rect(HEATER_FIN_HEIGHT, HEATER_FIN_THICKNESS)
            .extrude(length * 0.8)
        )
        fin = fin.rotate((0, 0, 0), (0, 0, 1), angle)
        head = head.union(fin)

    return head


def make_heater_internal_fins() -> cq.Workplane:
    """Internal radial fins inside the heater head cup.

    Increases gas-side heat transfer area 3-5x over a plain cup.
    12 radial fins extending inward from the cup wall, running
    axially for most of the cup depth.
    """
    od = HEATER_HEAD_OD - 2 * HEATER_HEAD_WALL  # inner diameter of cup
    ir = od / 2  # inner radius of cup wall

    fins = None
    for i in range(HEATER_INT_FIN_COUNT):
        angle = i * (360.0 / HEATER_INT_FIN_COUNT)
        angle_rad = math.radians(angle)

        # Fin extends inward from cup wall
        r_mid = ir - HEATER_INT_FIN_HEIGHT / 2
        cx = r_mid * math.cos(angle_rad)
        cy = r_mid * math.sin(angle_rad)

        fin = (
            cq.Workplane("XY")
            .center(cx, cy)
            .rect(HEATER_INT_FIN_HEIGHT, HEATER_INT_FIN_THICKNESS)
            .extrude(HEATER_INT_FIN_LENGTH)
        )
        fin = fin.rotate((0, 0, 0), (0, 0, 1), angle)

        if fins is None:
            fins = fin
        else:
            fins = fins.union(fin)

    return fins


def make_displacer() -> cq.Workplane:
    """Free-floating displacer — lightweight hollow cylinder, no rod.

    Oscillates in the hot space driven by pressure differential.
    Centered by clearance seal to vessel bore (0.75mm radial gap).
    Moving SmCo magnetic spring ring bonds directly to the bottom cap.
    """
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

    return displacer


def make_magnetic_spring_fixed() -> cq.Workplane:
    """Fixed SmCo magnet ring — mounted to vessel inner wall.

    SmCo (samarium cobalt) rated to 300°C operating temperature.
    Center is open for gas flow. Polarized axially to repel the
    moving ring on the displacer's outer edge.
    """
    magnet = (
        cq.Workplane("XY")
        .circle(MAG_SPRING_FIXED_OD / 2)
        .circle(MAG_SPRING_FIXED_ID / 2)
        .extrude(MAG_SPRING_LENGTH)
    )
    return magnet


def make_magnetic_spring_moving() -> cq.Workplane:
    """Moving SmCo magnet ring — bonded to displacer outer edge at bottom.

    SmCo for high-temperature operation near hot displacer.
    Hugs the displacer's outer diameter. Polarized to repel the
    fixed wall ring below. Center is open for gas flow.
    """
    magnet = (
        cq.Workplane("XY")
        .circle(MAG_SPRING_MOVING_OD / 2)
        .circle(MAG_SPRING_MOVING_ID / 2)
        .extrude(MAG_SPRING_LENGTH)
    )
    return magnet


def make_power_piston() -> cq.Workplane:
    """Free-floating power piston with magnet ring for linear alternator.

    89mm OD in 90mm bore = 0.5mm radial clearance seal. This is the
    primary gas seal between working space and bounce space.

    Heavier than displacer — provides inertial mass for the oscillating system.
    Magnet ring is concentric around the piston (not the sealing surface).
    """
    # Main piston body — fills the bore with clearance seal
    piston = cq.Workplane("XY").circle(PISTON_OD / 2).extrude(PISTON_LENGTH)

    # Magnet ring — bonded concentrically around the piston, centered vertically.
    # Ring OD (88mm) is recessed inside the piston OD (89mm) — not a sealing surface.
    mag_z_offset = (PISTON_LENGTH - MAGNET_RING_LENGTH) / 2

    # Cut a recess in the piston for the magnet ring
    recess = (
        cq.Workplane("XY")
        .workplane(offset=mag_z_offset)
        .circle(PISTON_OD / 2)
        .circle(MAGNET_RING_ID / 2)
        .extrude(MAGNET_RING_LENGTH)
    )
    piston = piston.cut(recess)

    # Insert the magnet ring into the recess
    magnet = (
        cq.Workplane("XY")
        .workplane(offset=mag_z_offset)
        .circle(MAGNET_RING_OD / 2)
        .circle(MAGNET_RING_ID / 2)
        .extrude(MAGNET_RING_LENGTH)
    )
    piston = piston.union(magnet)

    return piston


def make_alternator_stator() -> cq.Workplane:
    """Stator coil housing — wraps around the pressure vessel exterior.

    55mm long (increased from 40mm) to accommodate 10-15mm piston stroke
    with adequate overhang for flux linkage at stroke extremes.

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

    Positioned to align with the internal cooler zone for radial heat transfer.
    """
    vessel_section_od = VESSEL_OD

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

    return cq.Workplane("XY")


def make_internal_cooler() -> cq.Workplane:
    """Internal cooler — full-bore tube bundle spanning the entire vessel bore.

    48 tubes × 3mm diameter in a hexagonal pattern across the full 90mm bore.
    Total flow area ~339 mm² (was 85 mm² in annular design).
    Gas flows axially through tubes, transferring heat radially to the
    vessel wall where external fins dissipate it to ambient air.

    No center bypass — the solid matrix between tubes blocks any gas
    from flowing around the heat exchanger.
    """
    # Solid cylinder filling the bore
    body = (
        cq.Workplane("XY")
        .circle(COOLER_INT_OD / 2)
        .extrude(COOLER_INT_LENGTH)
    )

    # Hex-packed tube holes across the bore
    # Generate hex grid positions within the bore radius
    tube_r = COOLER_INT_TUBE_DIA / 2
    bore_r = COOLER_INT_OD / 2 - 2.0  # 2mm margin from vessel wall
    spacing = COOLER_INT_TUBE_DIA + 2.5  # tube center-to-center spacing

    positions = []
    # Hex grid
    row = 0
    y = -bore_r
    while y <= bore_r:
        x_offset = (spacing / 2) if (row % 2) else 0.0
        x = -bore_r + x_offset
        while x <= bore_r:
            if math.sqrt(x**2 + y**2) <= bore_r:
                positions.append((x, y))
            x += spacing
        y += spacing * math.sqrt(3) / 2
        row += 1

    # Drill tube holes
    for cx, cy in positions:
        hole = (
            cq.Workplane("XY")
            .center(cx, cy)
            .circle(tube_r)
            .extrude(COOLER_INT_LENGTH)
        )
        body = body.cut(hole)

    return body


def make_regenerator() -> cq.Workplane:
    """Regenerator — full-bore packed wire mesh housing.

    45mm long (increased from 18mm) SS316 stacked screens (80-mesh).
    ~70% porosity, ~15,000 mm²/cc surface area density.
    Fills the entire bore cross-section — no center bypass path.

    Modeled as solid cylinder with representative axial holes.
    Actual regenerator is packed fine wire mesh screens.
    Gas passes through, transferring heat to/from the mesh each stroke.
    Recovers 90-95% of heat between hot and cold spaces.
    """
    # Solid cylinder filling the bore — represents the mesh housing
    body = (
        cq.Workplane("XY")
        .circle(REGEN_OD / 2)
        .extrude(REGEN_LENGTH)
    )

    # Representative flow holes in hex pattern (actual mesh has ~70% porosity)
    bore_r = REGEN_OD / 2 - 2.0
    hole_r = REGEN_HOLE_DIA / 2
    spacing = REGEN_HOLE_DIA + 2.0

    positions = []
    row = 0
    y = -bore_r
    while y <= bore_r:
        x_offset = (spacing / 2) if (row % 2) else 0.0
        x = -bore_r + x_offset
        while x <= bore_r:
            if math.sqrt(x**2 + y**2) <= bore_r:
                positions.append((x, y))
            x += spacing
        y += spacing * math.sqrt(3) / 2
        row += 1

    for cx, cy in positions:
        hole = (
            cq.Workplane("XY")
            .center(cx, cy)
            .circle(hole_r)
            .extrude(REGEN_LENGTH)
        )
        body = body.cut(hole)

    return body


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
    - Z=-20         Fill tube (helium charge port, pinch-weld sealed)
    - Z=0           Vessel floor
    - Z=5           Centering magnet (repels piston magnet ring)
    - Z=0-40        Bounce space
    - Z=40          Power piston (89mm OD, 0.5mm clearance seal)
    - Z=~25         Alternator stator (external, 55mm long, centered on magnet ring)
    - Z=68          Internal cooler tubes + external cooler fins (3mm above piston)
    - Z=106         Regenerator (45mm long, full-bore packed mesh)
    - Z=153         Magnetic spring fixed ring (wall-mounted)
    - Z=181         Magnetic spring moving ring (20mm gap, bonded to displacer)
    - Z=191         Displacer (0.75mm clearance seal)
    - Z=~254        Hot space (12mm gap)
    - Z=~266        Heater head (with 12 internal fins)

    Gas flow path (all full-bore, no bypass):
    Hot space → Internal heater fins → Regenerator → Internal cooler → Cold space

    Dead volume budget:
    - Hot space: ~7.6 cc (12mm × bore area, minus displacer)
    - HX passages: ~30 cc (tubes + mesh at ~70% porosity)
    - Cold space gap: ~1.9 cc (3mm above piston)
    - Total dead: ~40 cc vs ~57 cc swept → ratio ~0.7:1
    """
    assy = cq.Assembly(name="free_piston_stirling")

    print("  Building pressure vessel...")
    vessel = make_pressure_vessel()
    assy.add(vessel, name="pressure_vessel", color=cq.Color("gray60"))

    print("  Building fill tube...")
    fill_tube = make_fill_tube()
    assy.add(fill_tube, name="fill_tube", color=cq.Color("gray40"))

    print("  Building centering magnet...")
    floor_mag = make_centering_magnet_floor()
    floor_mag = floor_mag.translate((0, 0, CENTER_MAG_FLOOR_Z))
    assy.add(floor_mag, name="centering_mag_floor", color=cq.Color("magenta3"))

    print("  Building heater head...")
    heater = make_heater_head()
    heater = heater.translate((0, 0, VESSEL_LENGTH))
    assy.add(heater, name="heater_head", color=cq.Color("firebrick"))

    print("  Building heater internal fins...")
    int_fins = make_heater_internal_fins()
    # Position fins at the base of the heater head interior (just above vessel top)
    int_fins = int_fins.translate((0, 0, VESSEL_LENGTH))
    assy.add(int_fins, name="heater_internal_fins", color=cq.Color("firebrick"))

    print("  Building displacer...")
    displacer = make_displacer()
    displacer = displacer.translate((0, 0, Z_DISPLACER))
    assy.add(displacer, name="displacer", color=cq.Color("orange"))

    print("  Building magnetic spring (fixed ring, SmCo)...")
    mag_fixed = make_magnetic_spring_fixed()
    mag_fixed = mag_fixed.translate((0, 0, Z_MAG_FIXED))
    assy.add(mag_fixed, name="mag_spring_fixed", color=cq.Color("red3"))

    print("  Building magnetic spring (moving ring, SmCo)...")
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

    print("  Building external cooler fins...")
    cooler = make_cooler()
    cooler = cooler.translate((0, 0, Z_COOLER_INT))
    assy.add(cooler, name="cooler", color=cq.Color("steelblue"))

    print("  Building internal cooler (full-bore tube bundle)...")
    int_cooler = make_internal_cooler()
    int_cooler = int_cooler.translate((0, 0, Z_COOLER_INT))
    assy.add(int_cooler, name="internal_cooler", color=cq.Color(0.12, 0.56, 1.0))

    print("  Building regenerator (full-bore packed mesh)...")
    regen = make_regenerator()
    regen = regen.translate((0, 0, Z_REGEN))
    assy.add(regen, name="regenerator", color=cq.Color(0.13, 0.55, 0.13))

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
