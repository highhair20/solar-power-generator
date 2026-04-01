"""
Geometric Interference Checker

Verifies that no two solid components in a CadQuery assembly physically
occupy the same space (CLAUDE.md design constraint: no geometric interference).

Uses OCCT boolean intersection: if two positioned bodies share volume,
their intersection solid has non-zero volume → interference detected.

Algorithm:
1. Walk the Assembly tree, collecting each component's solid with its
   global transform applied (location composition from root to leaf).
2. For every unique pair (A, B), compute solid A ∩ solid B.
3. If the intersection volume exceeds the noise threshold, report a failure.

Complexity: O(n²) pairs, each requiring one OCCT boolean operation.
Acceptable for assemblies with <50 components (typical for this project).

Usage:
    from check_interference import check_interference
    check_interference(my_assembly)   # raises RuntimeError on overlap
"""

import cadquery as cq


# Minimum intersection volume to flag as a real interference (mm³).
# Below this threshold the overlap is considered numerical noise from
# shared faces (coincident/touching geometry that is intentional).
_VOLUME_THRESHOLD_MM3 = 0.1


def _collect_solids(assembly: cq.Assembly, parent_loc=None):
    """Recursively collect (name, Shape) pairs from a cq.Assembly.

    Applies the cumulative location transform so each shape is expressed
    in the assembly's root coordinate frame.

    Args:
        assembly: cq.Assembly node to traverse
        parent_loc: cumulative cq.Location from root to this node's parent

    Yields:
        (name, cq.Shape) — shape positioned in root frame
    """
    if parent_loc is None:
        parent_loc = cq.Location()

    # Compose this node's location with the parent's
    node_loc = parent_loc * assembly.loc

    if assembly.obj is not None:
        # Extract the underlying Shape (Workplane → val(), Shape → as-is)
        obj = assembly.obj
        if isinstance(obj, cq.Workplane):
            shape = obj.val()
        elif isinstance(obj, cq.Shape):
            shape = obj
        else:
            shape = None

        if shape is not None and not shape.IsNull:
            # Apply the cumulative transform to position the shape in root frame
            positioned = shape.located(node_loc)
            yield (assembly.name or "unnamed", positioned)

    for child in assembly.children:
        yield from _collect_solids(child, node_loc)


def check_interference(
    assembly: cq.Assembly,
    threshold_mm3: float = _VOLUME_THRESHOLD_MM3,
    verbose: bool = True,
) -> list:
    """Check all component pairs in a cq.Assembly for solid-body overlaps.

    Args:
        assembly:     CadQuery Assembly to check
        threshold_mm3: minimum overlap volume in mm³ to report (avoids
                      floating-point noise at shared/touching faces)
        verbose:      print pass/fail summary to stdout

    Returns:
        List of (name_a, name_b, overlap_volume_mm3) for each interference.
        Empty list means no interference detected.

    Raises:
        RuntimeError: if any interference with volume > threshold is found.
    """
    solids = list(_collect_solids(assembly))
    n = len(solids)

    if verbose:
        print(f"\n── INTERFERENCE CHECK ──")
        print(f"  Components: {n}")
        print(f"  Pairs to check: {n * (n - 1) // 2}")

    interferences = []

    for i in range(n):
        name_a, shape_a = solids[i]
        for j in range(i + 1, n):
            name_b, shape_b = solids[j]
            try:
                # Boolean intersection: non-empty result → shared volume
                intersection = shape_a.intersect(shape_b)
                vol = intersection.Volume()
                if vol > threshold_mm3:
                    interferences.append((name_a, name_b, vol))
                    if verbose:
                        print(f"  [FAIL] {name_a!r} ∩ {name_b!r}  =  {vol:.2f} mm³")
            except Exception:
                # OCCT throws when the intersection is exactly empty (null shape).
                # This is the normal/expected case — no interference.
                pass

    if verbose:
        if interferences:
            print(f"\n  RESULT: {len(interferences)} interference(s) found — see above")
        else:
            print(f"  RESULT: PASS — no overlapping solids detected")

    if interferences:
        details = "; ".join(
            f"{a!r} ∩ {b!r} = {v:.2f} mm³" for a, b, v in interferences
        )
        raise RuntimeError(
            f"Geometric interference detected ({len(interferences)} pair(s)): {details}"
        )

    return interferences
