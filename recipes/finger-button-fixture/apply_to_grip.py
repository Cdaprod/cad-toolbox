#!/usr/bin/env python3
"""
Apply the same parametric Boolean fixture to three finger locations.

This script DOES NOT guess finger locations.

You place the fixture by editing placements.json. Each button gets XYZ and
Euler rotation values in degrees. This makes the operation deterministic and
version-controllable while you tune placement against the actual grip.

Usage:

    python apply_to_grip.py \
        path/to/grip.step \
        --placements recipes/finger-button-fixture/placements.json

Optional:
    --preview

The preview export writes transformed cap/switch/board/cutter STEP files for
each finger without modifying the input model.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
sys.path.insert(0, str(SRC))

from build123d import export_step

from cad_toolbox.fixtures.finger_button import (
    ButtonFixtureParams,
    apply_button_cutters,
    import_grip_step,
    load_placements,
    make_button_fixture,
    moved_fixture,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("grip", help="Input grip STEP file")
    parser.add_argument(
        "--placements",
        default=str(Path(__file__).with_name("placements.json")),
    )
    parser.add_argument(
        "--out",
        default="build/finger-button-fixture/grip_with_finger_buttons.step",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Export each transformed reference component before cutting.",
    )

    args = parser.parse_args()

    grip_path = Path(args.grip).expanduser().resolve()
    if not grip_path.exists():
        raise SystemExit(f"Input does not exist: {grip_path}")

    placements_path = Path(args.placements).expanduser().resolve()
    placements = load_placements(placements_path)

    if not placements:
        raise SystemExit("placements file contains no buttons")

    fixture = make_button_fixture(ButtonFixtureParams())
    grip = import_grip_step(grip_path)

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.preview:
        preview_dir = out.parent / "placement-preview"
        preview_dir.mkdir(parents=True, exist_ok=True)

        for spec in placements:
            f = moved_fixture(fixture, spec)
            export_step(f.cap, preview_dir / f"{spec.name}_cap.step")
            export_step(f.switch_ref, preview_dir / f"{spec.name}_switch.step")
            export_step(f.board_ref, preview_dir / f"{spec.name}_board.step")
            export_step(f.cutter, preview_dir / f"{spec.name}_cutter.step")

        print(f"Preview references: {preview_dir}")

    result = apply_button_cutters(grip, fixture, placements)
    export_step(result, out)

    print(f"Input:      {grip_path}")
    print(f"Placements: {placements_path}")
    print(f"Buttons:    {len(placements)}")
    print(f"Output:     {out}")


if __name__ == "__main__":
    main()
