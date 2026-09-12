#!/usr/bin/env python3
"""
Generate the reusable finger-button fixture/cutter.

Examples:

    python generate_fixture.py

    python generate_fixture.py \
        --cap-x 13 \
        --cap-y 11 \
        --board-x 10 \
        --board-y 12 \
        --switch-x 6 \
        --switch-y 4 \
        --switch-z 2.5

Output is written to:
    build/finger-button-fixture/
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
sys.path.insert(0, str(SRC))

from cad_toolbox.fixtures.finger_button import (
    ButtonFixtureParams,
    export_fixture,
    make_button_fixture,
)


def positive_float(value: str) -> float:
    result = float(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return result


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate a parametric near-flush finger-button CAD fixture."
    )

    p.add_argument("--out", default="build/finger-button-fixture")

    p.add_argument("--switch-x", type=positive_float, default=6.0)
    p.add_argument("--switch-y", type=positive_float, default=4.0)
    p.add_argument("--switch-z", type=positive_float, default=2.5)

    p.add_argument("--board-x", type=positive_float, default=10.0)
    p.add_argument("--board-y", type=positive_float, default=12.0)
    p.add_argument("--board-z", type=positive_float, default=1.0)

    p.add_argument("--cap-x", type=positive_float, default=13.0)
    p.add_argument("--cap-y", type=positive_float, default=11.0)
    p.add_argument("--cap-z", type=positive_float, default=1.8)

    p.add_argument("--flange-overhang", type=positive_float, default=0.8)
    p.add_argument("--flange-z", type=positive_float, default=1.0)

    p.add_argument("--stem-x", type=positive_float, default=4.0)
    p.add_argument("--stem-y", type=positive_float, default=4.0)
    p.add_argument("--stem-z", type=positive_float, default=2.0)

    p.add_argument("--cap-clearance", type=positive_float, default=0.25)
    p.add_argument("--switch-clearance", type=positive_float, default=0.30)
    p.add_argument("--board-clearance", type=positive_float, default=0.40)

    p.add_argument(
        "--no-stl",
        action="store_true",
        help="Export only STEP + JSON; skip STL meshes.",
    )

    return p


def main() -> None:
    args = parser().parse_args()

    params = ButtonFixtureParams(
        switch_x=args.switch_x,
        switch_y=args.switch_y,
        switch_z=args.switch_z,
        board_x=args.board_x,
        board_y=args.board_y,
        board_z=args.board_z,
        cap_x=args.cap_x,
        cap_y=args.cap_y,
        cap_z=args.cap_z,
        flange_overhang=args.flange_overhang,
        flange_z=args.flange_z,
        stem_x=args.stem_x,
        stem_y=args.stem_y,
        stem_z=args.stem_z,
        cap_xy_clearance=args.cap_clearance,
        switch_xy_clearance=args.switch_clearance,
        board_xy_clearance=args.board_clearance,
    )

    fixture = make_button_fixture(params)

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out

    paths = export_fixture(
        fixture,
        out,
        export_meshes=not args.no_stl,
    )

    print("\nGenerated finger-button fixture:")
    for name, path in paths.items():
        print(f"  {name:14s} {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
