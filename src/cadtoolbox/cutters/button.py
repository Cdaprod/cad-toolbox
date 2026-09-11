from dataclasses import dataclass

@dataclass(frozen=True)
class ButtonSpec:
    width: float
    depth: float
    height: float
    clearance: float = 0.25

    @property
    def cutter_size(self):
        return (
            self.width + 2 * self.clearance,
            self.depth + 2 * self.clearance,
            self.height,
        )

def build123d_button_cutter(spec: ButtonSpec):
    from build123d import Box, Align
    x, y, z = spec.cutter_size
    return Box(x, y, z, align=(Align.CENTER, Align.CENTER, Align.MIN))
