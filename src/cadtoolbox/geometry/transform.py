from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Transform:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0
    scale: float = 1.0

    def matrix(self) -> list[list[float]]:
        """Return a 4x4 transform matrix using XYZ Euler rotations in degrees."""
        sx = sy = sz = self.scale
        ax, ay, az = map(math.radians, (self.rx, self.ry, self.rz))
        cx, sxn = math.cos(ax), math.sin(ax)
        cy, syn = math.cos(ay), math.sin(ay)
        cz, szn = math.cos(az), math.sin(az)

        rx = [[1,0,0,0],[0,cx,-sxn,0],[0,sxn,cx,0],[0,0,0,1]]
        ry = [[cy,0,syn,0],[0,1,0,0],[-syn,0,cy,0],[0,0,0,1]]
        rz = [[cz,-szn,0,0],[szn,cz,0,0],[0,0,1,0],[0,0,0,1]]

        def mm(a, b):
            return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

        m = mm(rz, mm(ry, rx))
        m[0][0] *= sx; m[0][1] *= sx; m[0][2] *= sx
        m[1][0] *= sy; m[1][1] *= sy; m[1][2] *= sy
        m[2][0] *= sz; m[2][1] *= sz; m[2][2] *= sz
        m[0][3], m[1][3], m[2][3] = self.x, self.y, self.z
        return m
