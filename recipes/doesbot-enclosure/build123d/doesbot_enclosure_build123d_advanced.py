"""
DOESBOT CNC Controller Enclosure — build123d rewrite
====================================================

A clean, parametric two-piece enclosure for a ~127 x 85.725 mm controller PCB.

Improvements over the original OpenSCAD version:
- Structured dataclass configuration instead of global constants.
- Centered coordinate system for easier reference-model placement.
- Typed side/port definitions.
- Independent printable parts and reference/cutter/debug geometry.
- Proper BREP solids suitable for STEP export.
- Optional PCB adjustment slots.
- Parametric screw bosses, lid locating tongue/groove, vents, and connector cuts.
- Separate manufacturing exports and visual assembly layout.
- Assertions catch impossible parameter combinations before geometry is built.
- No dependency on FreeCAD or Blender.

Install:
    python -m pip install build123d

Run:
    python doesbot_enclosure_build123d.py

Outputs are written to ./exports/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Cylinder,
    Location,
    Part,
    Pos,
    Rot,
    export_step,
    export_stl,
    export_gltf,
)


# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

class Side(str, Enum):
    FRONT = "front"   # -Y
    BACK = "back"     # +Y
    LEFT = "left"     # -X
    RIGHT = "right"   # +X


@dataclass(frozen=True)
class PCBConfig:
    x: float = 127.000
    y: float = 85.725
    thickness: float = 1.60

    clearance_x: float = 6.0
    clearance_y: float = 6.0

    standoff_height: float = 7.0
    component_height: float = 18.0
    top_wire_clearance: float = 24.0

    hole_edge_x: float = 4.0
    hole_edge_y: float = 4.0

    boss_od: float = 8.0
    boss_hole_d: float = 3.2

    adjustment_slots: bool = True
    slot_travel: float = 4.0


@dataclass(frozen=True)
class CaseConfig:
    wall: float = 2.50
    bottom_floor: float = 2.50
    top_roof: float = 2.50
    corner_radius: float = 5.0

    # Additional vertical room above component envelope before the seam.
    seam_margin: float = 6.0

    case_screw_d: float = 3.2
    case_boss_od: float = 9.0
    case_boss_inset_from_inner_corner: float = 7.0

    lip_height: float = 3.0
    lip_thickness: float = 1.5
    lip_clearance: float = 0.30

    port_clearance: float = 1.0

    # Boolean overlap to avoid coplanar cutter failures.
    epsilon: float = 0.20


@dataclass(frozen=True)
class VentConfig:
    top_count: int = 9
    top_length: float = 52.0
    top_width: float = 2.4
    top_spacing: float = 5.0
    top_center_x_fraction: float = -0.15
    top_center_y_fraction: float = 0.0

    bottom_count: int = 7
    bottom_length: float = 42.0
    bottom_width: float = 2.0
    bottom_spacing: float = 5.0
    bottom_center_x_fraction: float = 0.18
    bottom_center_y_fraction: float = 0.0


@dataclass(frozen=True)
class Port:
    name: str
    side: Side

    # Position along the wall measured in the enclosure-centered coordinate
    # system. FRONT/BACK use X. LEFT/RIGHT use Y.
    center: float

    width: float
    z: float
    height: float

    enabled: bool = True
    extra_clearance: float = 0.0


@dataclass
class EnclosureConfig:
    pcb: PCBConfig = field(default_factory=PCBConfig)
    case: CaseConfig = field(default_factory=CaseConfig)
    vents: VentConfig = field(default_factory=VentConfig)
    ports: list[Port] = field(default_factory=list)

    @property
    def inner_x(self) -> float:
        return self.pcb.x + 2 * self.pcb.clearance_x

    @property
    def inner_y(self) -> float:
        return self.pcb.y + 2 * self.pcb.clearance_y

    @property
    def outer_x(self) -> float:
        return self.inner_x + 2 * self.case.wall

    @property
    def outer_y(self) -> float:
        return self.inner_y + 2 * self.case.wall

    @property
    def pcb_origin_z(self) -> float:
        return self.case.bottom_floor + self.pcb.standoff_height

    @property
    def bottom_wall_height(self) -> float:
        return (
            self.pcb.standoff_height
            + self.pcb.thickness
            + self.pcb.component_height
            + self.case.seam_margin
        )

    @property
    def bottom_height(self) -> float:
        return self.case.bottom_floor + self.bottom_wall_height

    @property
    def top_wall_height(self) -> float:
        return self.pcb.top_wire_clearance

    @property
    def top_height(self) -> float:
        return self.top_wall_height + self.case.top_roof

    def validate(self) -> None:
        p, c = self.pcb, self.case

        assert p.x > 0 and p.y > 0 and p.thickness > 0
        assert c.wall > 0 and c.bottom_floor > 0 and c.top_roof > 0
        assert c.corner_radius > c.wall, (
            "corner_radius should exceed wall thickness for a clean inner radius"
        )
        assert 0 < c.lip_thickness < min(self.inner_x, self.inner_y) / 2
        assert c.lip_clearance >= 0
        assert c.lip_height > 0
        assert p.boss_od > p.boss_hole_d
        assert c.case_boss_od > c.case_screw_d

        min_boss_edge = c.case_boss_inset_from_inner_corner
        assert min_boss_edge > c.case_boss_od / 2

        for port in self.ports:
            if not port.enabled:
                continue
            assert port.width > 0 and port.height > 0, port.name


# -----------------------------------------------------------------------------
# DEFAULT DOESBOT PORT MAP
# -----------------------------------------------------------------------------

def default_config() -> EnclosureConfig:
    cfg = EnclosureConfig()

    # Original design used a lower-left coordinate system. This rewrite uses
    # enclosure center = (0,0), so convert those locations into center positions.
    pcb_left = -cfg.pcb.x / 2
    pcb_front = -cfg.pcb.y / 2

    cfg.ports = [
        Port(
            "front_a",
            Side.FRONT,
            center=pcb_left + 24 + 22 / 2,
            width=22,
            z=cfg.pcb_origin_z - 1,
            height=17,
        ),
        Port(
            "front_b",
            Side.FRONT,
            center=pcb_left + 65 + 26 / 2,
            width=26,
            z=cfg.pcb_origin_z - 1,
            height=17,
        ),
        Port(
            "back_a",
            Side.BACK,
            center=pcb_left + 22 + 24 / 2,
            width=24,
            z=cfg.pcb_origin_z - 1,
            height=17,
        ),
        Port(
            "back_b",
            Side.BACK,
            center=pcb_left + 82 + 24 / 2,
            width=24,
            z=cfg.pcb_origin_z - 1,
            height=17,
        ),
        Port(
            "left_a",
            Side.LEFT,
            center=pcb_front + 58 + 18 / 2,
            width=18,
            z=cfg.pcb_origin_z - 1,
            height=18,
        ),
        Port(
            "right_a",
            Side.RIGHT,
            center=pcb_front + 56 + 18 / 2,
            width=18,
            z=cfg.pcb_origin_z - 1,
            height=18,
        ),
    ]

    cfg.validate()
    return cfg


# -----------------------------------------------------------------------------
# PRIMITIVE GEOMETRY
# -----------------------------------------------------------------------------

def rounded_prism(x: float, y: float, z: float, radius: float) -> Part:
    """
    Robust rounded rectangular prism made from two boxes + four cylinders.

    This avoids depending on edge-selection/fillet topology and is therefore
    stable when dimensions change.
    """
    if min(x, y) <= 2 * radius:
        raise ValueError("radius too large for rounded prism")

    center = Box(
        x - 2 * radius,
        y,
        z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cross = Box(
        x,
        y - 2 * radius,
        z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    result = center + cross

    cx = x / 2 - radius
    cy = y / 2 - radius

    for px in (-cx, cx):
        for py in (-cy, cy):
            result += Pos(px, py, 0) * Cylinder(
                radius,
                z,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    return result


def slot_prism(
    overall_length: float,
    width: float,
    height: float,
    *,
    axis: Axis = Axis.X,
) -> Part:
    """
    Capsule/obround slot prism.
    """
    if overall_length < width:
        raise ValueError("slot overall_length must be >= slot width")

    straight = overall_length - width
    radius = width / 2

    if axis == Axis.X:
        body = Box(
            max(straight, 0.001),
            width,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        offset = straight / 2
        for x in (-offset, offset):
            body += Pos(x, 0, 0) * Cylinder(
                radius,
                height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        return body

    if axis == Axis.Y:
        body = Box(
            width,
            max(straight, 0.001),
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        offset = straight / 2
        for y in (-offset, offset):
            body += Pos(0, y, 0) * Cylinder(
                radius,
                height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        return body

    raise ValueError("slot_prism currently supports Axis.X or Axis.Y")


def ring_prism(
    outer_x: float,
    outer_y: float,
    thickness: float,
    height: float,
    outer_radius: float,
) -> Part:
    """
    Rounded rectangular ring, centered in XY and extending from Z=0 upward.
    """
    inner_x = outer_x - 2 * thickness
    inner_y = outer_y - 2 * thickness
    inner_radius = max(outer_radius - thickness, 0.25)

    outer = rounded_prism(outer_x, outer_y, height, outer_radius)
    inner = rounded_prism(
        inner_x,
        inner_y,
        height + 0.4,
        inner_radius,
    )
    inner = Pos(0, 0, -0.2) * inner
    return outer - inner


# -----------------------------------------------------------------------------
# PCB REFERENCE + PCB MOUNTS
# -----------------------------------------------------------------------------

def pcb_hole_positions(cfg: EnclosureConfig) -> list[tuple[float, float]]:
    p = cfg.pcb
    x = p.x / 2 - p.hole_edge_x
    y = p.y / 2 - p.hole_edge_y

    return [
        (-x, -y),
        (+x, -y),
        (-x, +y),
        (+x, +y),
    ]


def pcb_reference(cfg: EnclosureConfig) -> Part:
    p = cfg.pcb

    board = Box(
        p.x,
        p.y,
        p.thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    board = Pos(0, 0, cfg.pcb_origin_z) * board

    # Simplified component keep-out block.
    keepout = Box(
        p.x - 10,
        p.y - 10,
        p.component_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    keepout = Pos(
        0,
        0,
        cfg.pcb_origin_z + p.thickness,
    ) * keepout

    return board + keepout


def pcb_boss(cfg: EnclosureConfig) -> Part:
    p, c = cfg.pcb, cfg.case

    boss = Cylinder(
        p.boss_od / 2,
        p.standoff_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    if p.adjustment_slots:
        slot = slot_prism(
            p.boss_hole_d + p.slot_travel,
            p.boss_hole_d,
            p.standoff_height + 2 * c.epsilon,
            axis=Axis.X,
        )
        slot = Pos(0, 0, -c.epsilon) * slot
        return boss - slot

    hole = Cylinder(
        p.boss_hole_d / 2,
        p.standoff_height + 2 * c.epsilon,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    hole = Pos(0, 0, -c.epsilon) * hole
    return boss - hole


def pcb_mounts(cfg: EnclosureConfig) -> Part:
    result = None
    one = pcb_boss(cfg)

    for x, y in pcb_hole_positions(cfg):
        placed = Pos(x, y, cfg.case.bottom_floor) * one
        result = placed if result is None else result + placed

    return result


# -----------------------------------------------------------------------------
# CASE BOSSES
# -----------------------------------------------------------------------------

def case_boss_positions(cfg: EnclosureConfig) -> list[tuple[float, float]]:
    c = cfg.case

    # Inset measured inward from each INNER cavity corner.
    x = cfg.inner_x / 2 - c.case_boss_inset_from_inner_corner
    y = cfg.inner_y / 2 - c.case_boss_inset_from_inner_corner

    return [
        (-x, -y),
        (+x, -y),
        (-x, +y),
        (+x, +y),
    ]


def case_boss(
    cfg: EnclosureConfig,
    height: float,
    *,
    through_hole: bool = True,
) -> Part:
    c = cfg.case
    boss = Cylinder(
        c.case_boss_od / 2,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    if through_hole:
        hole = Cylinder(
            c.case_screw_d / 2,
            height + 2 * c.epsilon,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        hole = Pos(0, 0, -c.epsilon) * hole
        boss -= hole

    return boss


def case_boss_set(
    cfg: EnclosureConfig,
    height: float,
    z: float,
    *,
    through_hole: bool = True,
) -> Part:
    result = None
    one = case_boss(cfg, height, through_hole=through_hole)

    for x, y in case_boss_positions(cfg):
        placed = Pos(x, y, z) * one
        result = placed if result is None else result + placed

    return result


# -----------------------------------------------------------------------------
# PORT CUTTERS
# -----------------------------------------------------------------------------

def port_cutter(cfg: EnclosureConfig, port: Port) -> Part:
    c = cfg.case

    clearance = c.port_clearance + port.extra_clearance
    width = port.width + 2 * clearance
    height = port.height + 2 * clearance

    # Make the cutter substantially deeper than the wall so booleans are robust.
    depth = c.wall * 4 + 2 * c.epsilon
    z = port.z - clearance

    if port.side in (Side.FRONT, Side.BACK):
        cutter = Box(
            width,
            depth,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

        wall_y = cfg.outer_y / 2
        center_y = -wall_y if port.side == Side.FRONT else wall_y
        cutter = Pos(port.center, center_y, z) * cutter
        return cutter

    cutter = Box(
        depth,
        width,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    wall_x = cfg.outer_x / 2
    center_x = -wall_x if port.side == Side.LEFT else wall_x
    return Pos(center_x, port.center, z) * cutter


def all_port_cutters(cfg: EnclosureConfig) -> Part:
    result = None

    for port in cfg.ports:
        if not port.enabled:
            continue
        cutter = port_cutter(cfg, port)
        result = cutter if result is None else result + cutter

    if result is None:
        # Empty placeholder kept far away from the model.
        result = Pos(1_000_000, 0, 0) * Box(0.1, 0.1, 0.1)

    return result


# -----------------------------------------------------------------------------
# VENTS
# -----------------------------------------------------------------------------

def vent_bank(
    *,
    count: int,
    slot_length: float,
    slot_width: float,
    spacing: float,
    thickness: float,
    center_x: float,
    center_y: float,
    z: float,
) -> Part:
    if count <= 0:
        raise ValueError("vent count must be > 0")

    total_span = (count - 1) * spacing
    result = None

    for i in range(count):
        y = center_y - total_span / 2 + i * spacing
        slot = slot_prism(
            slot_length,
            slot_width,
            thickness,
            axis=Axis.X,
        )
        slot = Pos(center_x, y, z) * slot
        result = slot if result is None else result + slot

    return result


def bottom_vent_cutters(cfg: EnclosureConfig) -> Part:
    v, c = cfg.vents, cfg.case

    return vent_bank(
        count=v.bottom_count,
        slot_length=v.bottom_length,
        slot_width=v.bottom_width,
        spacing=v.bottom_spacing,
        thickness=c.bottom_floor + 2 * c.epsilon,
        center_x=v.bottom_center_x_fraction * cfg.outer_x,
        center_y=v.bottom_center_y_fraction * cfg.outer_y,
        z=-c.epsilon,
    )


def top_vent_cutters(cfg: EnclosureConfig) -> Part:
    v, c = cfg.vents, cfg.case

    return vent_bank(
        count=v.top_count,
        slot_length=v.top_length,
        slot_width=v.top_width,
        spacing=v.top_spacing,
        thickness=c.top_roof + 2 * c.epsilon,
        center_x=v.top_center_x_fraction * cfg.outer_x,
        center_y=v.top_center_y_fraction * cfg.outer_y,
        z=cfg.top_wall_height - c.epsilon,
    )


# -----------------------------------------------------------------------------
# BOTTOM
# -----------------------------------------------------------------------------

def bottom_shell(cfg: EnclosureConfig) -> Part:
    c = cfg.case

    outer = rounded_prism(
        cfg.outer_x,
        cfg.outer_y,
        cfg.bottom_height,
        c.corner_radius,
    )

    inner_radius = max(c.corner_radius - c.wall, 0.5)
    cavity = rounded_prism(
        cfg.inner_x,
        cfg.inner_y,
        cfg.bottom_height - c.bottom_floor + c.epsilon,
        inner_radius,
    )
    cavity = Pos(0, 0, c.bottom_floor) * cavity

    return outer - cavity


def bottom_locating_lip(cfg: EnclosureConfig) -> Part:
    c = cfg.case

    lip = ring_prism(
        cfg.inner_x,
        cfg.inner_y,
        c.lip_thickness,
        c.lip_height,
        max(c.corner_radius - c.wall, 0.5),
    )

    return Pos(
        0,
        0,
        cfg.bottom_height - c.lip_height,
    ) * lip


def build_bottom(cfg: EnclosureConfig) -> Part:
    cfg.validate()
    c = cfg.case

    body = bottom_shell(cfg)
    body += pcb_mounts(cfg)

    # Bottom case bosses rise from the floor to the seam.
    body += case_boss_set(
        cfg,
        height=cfg.bottom_wall_height,
        z=c.bottom_floor,
        through_hole=True,
    )

    body += bottom_locating_lip(cfg)

    body -= all_port_cutters(cfg)
    body -= bottom_vent_cutters(cfg)

    return body


# -----------------------------------------------------------------------------
# TOP / LID
# -----------------------------------------------------------------------------

def top_outer_shell(cfg: EnclosureConfig) -> Part:
    c = cfg.case

    outer = rounded_prism(
        cfg.outer_x,
        cfg.outer_y,
        cfg.top_height,
        c.corner_radius,
    )

    inner = rounded_prism(
        cfg.inner_x,
        cfg.inner_y,
        cfg.top_wall_height + c.epsilon,
        max(c.corner_radius - c.wall, 0.5),
    )
    inner = Pos(0, 0, -c.epsilon) * inner

    return outer - inner


def top_lip_clearance(cfg: EnclosureConfig) -> Part:
    """
    Female groove for the bottom locating tongue.

    Clearance is applied to both sides of the tongue so the lid can be printed
    in PLA/PETG without requiring a zero-clearance press fit.
    """
    c = cfg.case

    outer_x = cfg.inner_x + 2 * c.lip_clearance
    outer_y = cfg.inner_y + 2 * c.lip_clearance

    groove_thickness = c.lip_thickness + 2 * c.lip_clearance
    outer_radius = max(
        c.corner_radius - c.wall + c.lip_clearance,
        0.5,
    )

    groove = ring_prism(
        outer_x,
        outer_y,
        groove_thickness,
        c.lip_height + 2 * c.epsilon,
        outer_radius,
    )

    return Pos(0, 0, -c.epsilon) * groove


def top_screw_holes(cfg: EnclosureConfig) -> Part:
    c = cfg.case
    result = None

    hole = Cylinder(
        c.case_screw_d / 2,
        cfg.top_height + 2 * c.epsilon,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    hole = Pos(0, 0, -c.epsilon) * hole

    for x, y in case_boss_positions(cfg):
        placed = Pos(x, y, 0) * hole
        result = placed if result is None else result + placed

    return result


def build_top(cfg: EnclosureConfig) -> Part:
    cfg.validate()
    c = cfg.case

    body = top_outer_shell(cfg)

    # Internal columns connect the roof area to the bottom's case bosses.
    body += case_boss_set(
        cfg,
        height=cfg.top_wall_height,
        z=0,
        through_hole=True,
    )

    body -= top_lip_clearance(cfg)
    body -= top_screw_holes(cfg)
    body -= top_vent_cutters(cfg)

    return body


# -----------------------------------------------------------------------------
# DEBUG / ASSEMBLY
# -----------------------------------------------------------------------------

def build_cutters(cfg: EnclosureConfig) -> Part:
    return all_port_cutters(cfg) + bottom_vent_cutters(cfg)


def assembly_compound(
    cfg: EnclosureConfig,
    *,
    exploded: bool = False,
) -> Compound:
    bottom = build_bottom(cfg)
    pcb = pcb_reference(cfg)
    top = build_top(cfg)

    pcb_z_offset = 10.0 if exploded else 0.0
    top_z = cfg.bottom_height + (30.0 if exploded else 0.0)

    return Compound(
        children=[
            bottom,
            Pos(0, 0, pcb_z_offset) * pcb,
            Pos(0, 0, top_z) * top,
        ]
    )


def print_layout(cfg: EnclosureConfig, gap: float = 12.0) -> Compound:
    """
    Place bottom and lid next to each other for slicer/CAM inspection.

    The top is rotated 180 degrees around X so its roof sits on Z=0 and the
    open side faces upward for a conventional print orientation.
    """
    bottom = build_bottom(cfg)
    top = build_top(cfg)

    # build_top spans Z=0..top_height. Flip around X, then translate upward.
    top_print = Pos(
        cfg.outer_x + gap,
        0,
        cfg.top_height,
    ) * Rot(180, 0, 0) * top

    bottom_print = Pos(0, 0, 0) * bottom

    return Compound(children=[bottom_print, top_print])


# -----------------------------------------------------------------------------
# EXPORT
# -----------------------------------------------------------------------------

def export_all(
    cfg: EnclosureConfig,
    export_dir: Path = Path("exports") / "doesbot-enclosure",
    *,
    export_meshes: bool = True,
) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)

    bottom = build_bottom(cfg)
    top = build_top(cfg)
    pcb = pcb_reference(cfg)
    assembled = assembly_compound(cfg)
    exploded = assembly_compound(cfg, exploded=True)
    printable = print_layout(cfg)

    # Authoritative CAD exports
    export_step(bottom, export_dir / "doesbot-bottom.step")
    export_step(top, export_dir / "doesbot-top.step")
    export_step(pcb, export_dir / "doesbot-pcb-reference.step")
    export_step(assembled, export_dir / "doesbot-assembly.step")
    export_step(exploded, export_dir / "doesbot-exploded.step")
    export_step(printable, export_dir / "doesbot-print-layout.step")

    # Browser-friendly preview of the assembled model.
    # This uses the existing in-memory assembly; it does not create
    # another STEP file or re-import any exported geometry.
    export_gltf(
        assembled,
        export_dir / "doesbot-assembly.glb",
        binary=True,
        linear_deflection=0.1,
        angular_deflection=0.1,
    )

    if export_meshes:
        # STL parts only; GLB is used for browser inspection of the assembly.
        export_stl(bottom, export_dir / "doesbot-bottom.stl")
        export_stl(top, export_dir / "doesbot-top.stl")

    print("Generated DOESBOT enclosure:")
    print(f"  PCB:              {cfg.pcb.x:.3f} x {cfg.pcb.y:.3f} mm")
    print(f"  Inner cavity:     {cfg.inner_x:.3f} x {cfg.inner_y:.3f} mm")
    print(f"  Outer footprint:  {cfg.outer_x:.3f} x {cfg.outer_y:.3f} mm")
    print(f"  Bottom height:    {cfg.bottom_height:.3f} mm")
    print(f"  Lid height:       {cfg.top_height:.3f} mm")
    print(f"  Overall closed:   {cfg.bottom_height + cfg.top_height:.3f} mm")
    print(f"  Output:           {export_dir.resolve()}")
    print(f"  Browser preview:  {(export_dir / 'doesbot-assembly.glb').resolve()}")
 
# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    config = default_config()
    export_all(config)
