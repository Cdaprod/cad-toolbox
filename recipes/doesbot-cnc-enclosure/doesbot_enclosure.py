from dataclasses import dataclass
from pathlib import Path
from build123d import Align, Box, Cylinder, Compound, Pos, export_step, export_stl

@dataclass(frozen=True)
class Config:
    pcb_x: float = 127.0
    pcb_y: float = 85.725
    pcb_z: float = 1.6
    clear_x: float = 6.0
    clear_y: float = 6.0
    standoff: float = 7.0
    components: float = 18.0
    wire_clearance: float = 24.0
    wall: float = 2.5
    floor: float = 2.5
    roof: float = 2.5
    radius: float = 5.0
    seam_margin: float = 6.0
    pcb_boss_od: float = 8.0
    pcb_hole_d: float = 3.2
    case_boss_od: float = 9.0
    case_hole_d: float = 3.2

    @property
    def inner_x(self): return self.pcb_x + 2*self.clear_x
    @property
    def inner_y(self): return self.pcb_y + 2*self.clear_y
    @property
    def outer_x(self): return self.inner_x + 2*self.wall
    @property
    def outer_y(self): return self.inner_y + 2*self.wall
    @property
    def bottom_h(self): return self.floor + self.standoff + self.pcb_z + self.components + self.seam_margin
    @property
    def top_h(self): return self.wire_clearance + self.roof

def rounded_box(x, y, z, r):
    a = Box(x-2*r, y, z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    b = Box(x, y-2*r, z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    out = a + b
    for px in (-x/2+r, x/2-r):
        for py in (-y/2+r, y/2-r):
            out += Pos(px, py, 0) * Cylinder(r, z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return out

def pcb_mount_positions(c):
    x = c.pcb_x/2 - 4
    y = c.pcb_y/2 - 4
    return [(-x,-y),(x,-y),(-x,y),(x,y)]

def case_mount_positions(c):
    x = c.inner_x/2 - 7
    y = c.inner_y/2 - 7
    return [(-x,-y),(x,-y),(-x,y),(x,y)]

def bottom(c):
    outer = rounded_box(c.outer_x, c.outer_y, c.bottom_h, c.radius)
    cavity = Pos(0,0,c.floor) * rounded_box(
        c.inner_x, c.inner_y, c.bottom_h, max(c.radius-c.wall, 0.5)
    )
    body = outer - cavity

    for x,y in pcb_mount_positions(c):
        boss = Cylinder(c.pcb_boss_od/2, c.standoff, align=(Align.CENTER,Align.CENTER,Align.MIN))
        hole = Pos(0,0,-0.2) * Cylinder(c.pcb_hole_d/2, c.standoff+0.4,
                                       align=(Align.CENTER,Align.CENTER,Align.MIN))
        body += Pos(x,y,c.floor) * (boss-hole)

    case_h = c.bottom_h-c.floor
    for x,y in case_mount_positions(c):
        boss = Cylinder(c.case_boss_od/2, case_h, align=(Align.CENTER,Align.CENTER,Align.MIN))
        hole = Pos(0,0,-0.2) * Cylinder(c.case_hole_d/2, case_h+0.4,
                                       align=(Align.CENTER,Align.CENTER,Align.MIN))
        body += Pos(x,y,c.floor) * (boss-hole)
    return body

def top(c):
    outer = rounded_box(c.outer_x, c.outer_y, c.top_h, c.radius)
    cavity = Pos(0,0,-0.2) * rounded_box(
        c.inner_x, c.inner_y, c.wire_clearance+0.2, max(c.radius-c.wall,0.5)
    )
    body = outer-cavity
    for x,y in case_mount_positions(c):
        boss = Cylinder(c.case_boss_od/2, c.wire_clearance,
                        align=(Align.CENTER,Align.CENTER,Align.MIN))
        hole = Pos(0,0,-0.2) * Cylinder(c.case_hole_d/2, c.top_h+0.4,
                                       align=(Align.CENTER,Align.CENTER,Align.MIN))
        body += Pos(x,y,0) * boss
        body -= Pos(x,y,0) * hole
    return body

if __name__ == "__main__":
    c = Config()
    out = Path("exports")
    out.mkdir(exist_ok=True)
    b, t = bottom(c), top(c)
    export_step(b, out/"doesbot-bottom.step")
    export_step(t, out/"doesbot-top.step")
    export_stl(b, out/"doesbot-bottom.stl")
    export_stl(t, out/"doesbot-top.stl")
    export_step(Compound(children=[b, Pos(0,0,c.bottom_h)*t]), out/"doesbot-assembly.step")
    print(out.resolve())
