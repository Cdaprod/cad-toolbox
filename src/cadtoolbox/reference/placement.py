from dataclasses import dataclass

@dataclass(frozen=True)
class Placement:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0

def as_build123d_location(p: Placement):
    from build123d import Location
    return Location((p.x, p.y, p.z), (p.rx, p.ry, p.rz))
