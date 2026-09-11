from dataclasses import dataclass

@dataclass(frozen=True)
class FastenerClearance:
    shaft_diameter: float
    head_diameter: float | None = None
    head_depth: float = 0.0
    clearance: float = 0.2

def build123d_fastener_cutter(spec: FastenerClearance, depth: float):
    from build123d import Cylinder, Align, Pos
    shaft = Cylinder(
        (spec.shaft_diameter + 2 * spec.clearance) / 2,
        depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    if spec.head_diameter and spec.head_depth > 0:
        head = Cylinder(
            (spec.head_diameter + 2 * spec.clearance) / 2,
            spec.head_depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        shaft += Pos(0, 0, depth - spec.head_depth) * head
    return shaft
