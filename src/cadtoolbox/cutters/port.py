from dataclasses import dataclass

@dataclass(frozen=True)
class PortSpec:
    width: float
    height: float
    depth: float
    clearance: float = 0.30
    corner_radius: float = 0.0

def build123d_port_cutter(spec: PortSpec):
    from build123d import Box, Align
    w = spec.width + 2 * spec.clearance
    h = spec.height + 2 * spec.clearance
    d = spec.depth
    cutter = Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if spec.corner_radius > 0:
        # Keep construction robust: fillet only vertical edges.
        try:
            cutter = cutter.fillet(spec.corner_radius, cutter.edges().filter_by("Z"))
        except Exception:
            pass
    return cutter
