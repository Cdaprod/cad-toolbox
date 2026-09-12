"""
Parametric near-flush finger-button fixture for ergonomic grips.

This module generates:
- printable cap
- switch reference body
- perfboard reference body
- Boolean cutter/relief body
- optional three-button application to a STEP grip

Coordinate convention
---------------------
Local +Z points OUTWARD from the grip surface.
The grip wall is nominally centered around Z=0.
The switch/board live toward -Z (inside the grip).

The fixture is intentionally modeled as coordinated solids so that the same
placement can be used for:
    cap
    switch reference
    board reference
    cutter

Dependencies:
    build123d
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence
import json

from build123d import (
    Align,
    Box,
    BuildPart,
    Location,
    Mode,
    Part,
    Pos,
    Rot,
    export_step,
    export_stl,
    import_step,
)


@dataclass(frozen=True)
class ButtonFixtureParams:
    # ------------------------------------------------------------------
    # Actual hardware
    # ------------------------------------------------------------------
    switch_x: float = 6.0
    switch_y: float = 4.0
    switch_z: float = 2.5

    board_x: float = 10.0
    board_y: float = 12.0
    board_z: float = 1.0

    # ------------------------------------------------------------------
    # Printed cap
    # ------------------------------------------------------------------
    cap_x: float = 13.0
    cap_y: float = 11.0
    cap_z: float = 1.8

    # The hidden flange is larger than the opening so the cap cannot
    # fall outward through the grip.
    flange_overhang: float = 0.8
    flange_z: float = 1.0

    # Stem couples cap motion to the tactile switch.
    stem_x: float = 4.0
    stem_y: float = 4.0
    stem_z: float = 2.0

    # ------------------------------------------------------------------
    # Fit / print clearances
    # ------------------------------------------------------------------
    cap_xy_clearance: float = 0.25
    flange_xy_clearance: float = 0.25
    stem_xy_clearance: float = 0.25
    switch_xy_clearance: float = 0.30
    board_xy_clearance: float = 0.40

    # Extra depth prevents coincident Boolean faces.
    boolean_z_overlap: float = 0.30

    # Gap between back of flange and top of switch body.
    switch_gap: float = 0.25

    # Depth behind board left open for solder/wire bend.
    rear_wire_relief_z: float = 2.5

    # Extra XY space behind board for solder blobs and wiring.
    rear_wire_relief_xy: float = 1.0

    def validate(self) -> None:
        dims = asdict(self)
        bad = [name for name, value in dims.items() if value <= 0]
        if bad:
            raise ValueError(f"All parameters must be > 0; invalid: {bad}")

        if self.cap_x <= self.stem_x or self.cap_y <= self.stem_y:
            raise ValueError("cap_x/cap_y must be larger than stem_x/stem_y")

        if self.board_x < self.switch_x or self.board_y < self.switch_y:
            raise ValueError("Board must be at least as large as switch footprint")

        if self.flange_overhang <= self.cap_xy_clearance:
            raise ValueError(
                "flange_overhang should exceed cap_xy_clearance so the cap "
                "cannot pass through the outer opening"
            )


@dataclass
class ButtonFixture:
    params: ButtonFixtureParams
    cap: Part
    switch_ref: Part
    board_ref: Part
    cutter: Part


@dataclass(frozen=True)
class PlacementSpec:
    """Fixture placement relative to the imported grip."""

    name: str
    x: float
    y: float
    z: float
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0

    def location(self) -> Location:
        # Pos * Rot produces a local placement:
        # first orient the fixture, then position it.
        return Pos(self.x, self.y, self.z) * Rot(self.rx, self.ry, self.rz)


def _centered_box(x: float, y: float, z: float) -> Part:
    """Box centered on X/Y with its bottom at local Z=0."""
    with BuildPart() as bp:
        Box(
            x,
            y,
            z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    return bp.part


def _move(part: Part, x: float = 0, y: float = 0, z: float = 0) -> Part:
    return part.moved(Pos(x, y, z))


def make_button_fixture(params: ButtonFixtureParams | None = None) -> ButtonFixture:
    """
    Build one complete coordinated button fixture.

    Z stack, outside -> inside:

        +Z
          cap face
        --------------------- nominal grip outside
          flange
          stem
          switch
          board
          rear wire relief
        -Z
    """
    p = params or ButtonFixtureParams()
    p.validate()

    # ------------------------------------------------------------------
    # CAP
    # ------------------------------------------------------------------
    # Visible cap top begins at nominal grip surface Z=0 and extends outward.
    cap_face = _centered_box(p.cap_x, p.cap_y, p.cap_z)

    # Hidden retaining flange lives immediately behind the grip skin.
    flange_x = p.cap_x + 2 * p.flange_overhang
    flange_y = p.cap_y + 2 * p.flange_overhang
    flange = _centered_box(flange_x, flange_y, p.flange_z)
    flange = _move(flange, z=-p.flange_z)

    # Stem starts at the back of the retaining flange.
    stem = _centered_box(p.stem_x, p.stem_y, p.stem_z)
    stem = _move(stem, z=-(p.flange_z + p.stem_z))

    cap = cap_face + flange + stem

    # ------------------------------------------------------------------
    # SWITCH + BOARD REFERENCE BODIES
    # ------------------------------------------------------------------
    switch_top_z = -(p.flange_z + p.stem_z + p.switch_gap)
    switch_bottom_z = switch_top_z - p.switch_z

    switch_ref = _centered_box(p.switch_x, p.switch_y, p.switch_z)
    switch_ref = _move(switch_ref, z=switch_bottom_z)

    board_top_z = switch_bottom_z
    board_bottom_z = board_top_z - p.board_z

    board_ref = _centered_box(p.board_x, p.board_y, p.board_z)
    board_ref = _move(board_ref, z=board_bottom_z)

    # ------------------------------------------------------------------
    # BOOLEAN CUTTER
    # ------------------------------------------------------------------
    # A stepped cutter is intentionally generated instead of subtracting
    # the exact hardware models. Every cavity gets manufacturing clearance.

    # 1. Outer cap opening.
    # It runs through Z=0 to guarantee a clean through-cut at the grip skin.
    cap_open_x = p.cap_x + 2 * p.cap_xy_clearance
    cap_open_y = p.cap_y + 2 * p.cap_xy_clearance
    cap_open_z = p.cap_z + p.flange_z + 2 * p.boolean_z_overlap

    cap_open = _centered_box(cap_open_x, cap_open_y, cap_open_z)
    cap_open = _move(
        cap_open,
        z=-(p.flange_z + p.boolean_z_overlap),
    )

    # 2. Flange travel / retaining relief.
    flange_relief_x = flange_x + 2 * p.flange_xy_clearance
    flange_relief_y = flange_y + 2 * p.flange_xy_clearance
    flange_relief_z = p.flange_z + p.boolean_z_overlap

    flange_relief = _centered_box(
        flange_relief_x,
        flange_relief_y,
        flange_relief_z,
    )
    flange_relief = _move(
        flange_relief,
        z=-(p.flange_z + p.boolean_z_overlap),
    )

    # 3. Stem travel.
    stem_relief = _centered_box(
        p.stem_x + 2 * p.stem_xy_clearance,
        p.stem_y + 2 * p.stem_xy_clearance,
        p.stem_z + p.switch_gap + 2 * p.boolean_z_overlap,
    )
    stem_relief = _move(
        stem_relief,
        z=-(p.flange_z + p.stem_z + p.switch_gap + p.boolean_z_overlap),
    )

    # 4. Switch body clearance.
    switch_relief = _centered_box(
        p.switch_x + 2 * p.switch_xy_clearance,
        p.switch_y + 2 * p.switch_xy_clearance,
        p.switch_z + 2 * p.boolean_z_overlap,
    )
    switch_relief = _move(
        switch_relief,
        z=switch_bottom_z - p.boolean_z_overlap,
    )

    # 5. Perfboard pocket.
    board_relief = _centered_box(
        p.board_x + 2 * p.board_xy_clearance,
        p.board_y + 2 * p.board_xy_clearance,
        p.board_z + 2 * p.boolean_z_overlap,
    )
    board_relief = _move(
        board_relief,
        z=board_bottom_z - p.boolean_z_overlap,
    )

    # 6. Rear solder/wire relief.
    wire_relief = _centered_box(
        p.board_x + 2 * p.rear_wire_relief_xy,
        p.board_y + 2 * p.rear_wire_relief_xy,
        p.rear_wire_relief_z + p.boolean_z_overlap,
    )
    wire_relief = _move(
        wire_relief,
        z=board_bottom_z - p.rear_wire_relief_z,
    )

    cutter = (
        cap_open
        + flange_relief
        + stem_relief
        + switch_relief
        + board_relief
        + wire_relief
    )

    return ButtonFixture(
        params=p,
        cap=cap,
        switch_ref=switch_ref,
        board_ref=board_ref,
        cutter=cutter,
    )


def moved_fixture(fixture: ButtonFixture, placement: PlacementSpec) -> ButtonFixture:
    """Return a copy of a fixture transformed to one finger location."""
    loc = placement.location()
    return ButtonFixture(
        params=fixture.params,
        cap=fixture.cap.moved(loc),
        switch_ref=fixture.switch_ref.moved(loc),
        board_ref=fixture.board_ref.moved(loc),
        cutter=fixture.cutter.moved(loc),
    )


def apply_button_cutters(
    grip: Part,
    fixture: ButtonFixture,
    placements: Sequence[PlacementSpec],
) -> Part:
    """Subtract one fixture cutter at every requested placement."""
    result = grip

    for spec in placements:
        moved = moved_fixture(fixture, spec)
        result = result - moved.cutter

    return result


def load_placements(path: str | Path) -> list[PlacementSpec]:
    path = Path(path)
    data = json.loads(path.read_text())

    records = data["buttons"] if isinstance(data, dict) else data

    return [
        PlacementSpec(
            name=str(item.get("name", f"button_{index + 1}")),
            x=float(item["x"]),
            y=float(item["y"]),
            z=float(item["z"]),
            rx=float(item.get("rx", 0.0)),
            ry=float(item.get("ry", 0.0)),
            rz=float(item.get("rz", 0.0)),
        )
        for index, item in enumerate(records)
    ]


def export_fixture(
    fixture: ButtonFixture,
    out_dir: str | Path,
    prefix: str = "finger_button",
    export_meshes: bool = True,
) -> dict[str, Path]:
    """Export reusable fixture components."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = {
        "cap_step": out / f"{prefix}_cap.step",
        "switch_step": out / f"{prefix}_switch_ref.step",
        "board_step": out / f"{prefix}_board_ref.step",
        "cutter_step": out / f"{prefix}_cutter.step",
        "params_json": out / f"{prefix}_params.json",
    }

    export_step(fixture.cap, paths["cap_step"])
    export_step(fixture.switch_ref, paths["switch_step"])
    export_step(fixture.board_ref, paths["board_step"])
    export_step(fixture.cutter, paths["cutter_step"])

    paths["params_json"].write_text(
        json.dumps(asdict(fixture.params), indent=2) + "\n"
    )

    if export_meshes:
        paths.update(
            {
                "cap_stl": out / f"{prefix}_cap.stl",
                "switch_stl": out / f"{prefix}_switch_ref.stl",
                "board_stl": out / f"{prefix}_board_ref.stl",
                "cutter_stl": out / f"{prefix}_cutter.stl",
            }
        )
        export_stl(fixture.cap, paths["cap_stl"])
        export_stl(fixture.switch_ref, paths["switch_stl"])
        export_stl(fixture.board_ref, paths["board_stl"])
        export_stl(fixture.cutter, paths["cutter_stl"])

    return paths


def import_grip_step(path: str | Path) -> Part:
    return import_step(str(path))
