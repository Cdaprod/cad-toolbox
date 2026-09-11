from dataclasses import dataclass

@dataclass(frozen=True)
class Envelope:
    x: float
    y: float
    z: float
    clearance_x: float = 0.0
    clearance_y: float = 0.0
    clearance_z: float = 0.0

    @property
    def size(self):
        return (
            self.x + 2 * self.clearance_x,
            self.y + 2 * self.clearance_y,
            self.z + 2 * self.clearance_z,
        )
