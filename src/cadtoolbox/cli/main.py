from __future__ import annotations
import argparse
import json
from pathlib import Path

from cadtoolbox.backends import backend_status
from cadtoolbox.geometry.align import align_mesh
from cadtoolbox.geometry.bounds import mesh_bounds
from cadtoolbox.geometry.measure import mesh_measurements
from cadtoolbox.geometry.scale import scale_mesh
from cadtoolbox.io.convert import convert
from cadtoolbox.mesh.manifold import inspect_manifold
from cadtoolbox.mesh.repair import repair_mesh
from cadtoolbox.model import Model
from cadtoolbox.solid.boolean import boolean_step

def jprint(value):
    print(json.dumps(value, indent=2))

def cmd_backend(_args):
    jprint(backend_status())

def cmd_inspect(args):
    m = Model.from_path(args.file).require_exists()
    info = {
        "path": str(m.path),
        "suffix": m.suffix,
        "kind": m.kind,
        "bytes": m.path.stat().st_size,
    }
    if m.kind == "mesh":
        info["bounds"] = mesh_bounds(m.path)
        info["measurements"] = mesh_measurements(m.path)
        info["manifold"] = inspect_manifold(m.path)
    jprint(info)

def cmd_bounds(args):
    jprint(mesh_bounds(args.file))

def cmd_convert(args):
    out = convert(args.source, args.destination, linear_deflection=args.linear_deflection)
    print(out)

def cmd_scale(args):
    print(scale_mesh(args.source, args.destination, args.factor))

def cmd_align(args):
    print(align_mesh(
        args.source,
        args.destination,
        center_x=args.center_x,
        center_y=args.center_y,
        center_xy=args.center_xy,
        bottom_z=args.bottom_z,
    ))

def cmd_repair(args):
    jprint(repair_mesh(args.source, args.destination))

def cmd_boolean(args):
    print(boolean_step(
        args.operation,
        args.a,
        args.b,
        args.output,
        engine=args.engine,
    ))

def cmd_step_info(args):
    m = Model.from_path(args.file).require_exists()
    if m.suffix not in {".step", ".stp"}:
        raise SystemExit("step-info expects .step or .stp")
    print(f"path: {m.path}")
    print("STEP structure introspection is backend-dependent.")
    print("Use build123d/CadQuery/FreeCAD adapters for deeper inspection.")

def cmd_make_button_array(args):
    from build123d import Align, Box, Compound, Pos, export_step
    button = Box(args.width, args.depth, args.height,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    parts = [Pos(i * args.spacing, 0, 0) * button for i in range(args.count)]
    export_step(Compound(children=parts), args.output)
    print(args.output)

def cmd_make_port_cutter(args):
    from cadtoolbox.cutters.port import PortSpec, build123d_port_cutter
    from build123d import export_step
    shape = build123d_port_cutter(PortSpec(
        width=args.width,
        height=args.height,
        depth=args.depth,
        clearance=args.clearance,
        corner_radius=args.corner_radius,
    ))
    export_step(shape, args.output)
    print(args.output)

def build_parser():
    parser = argparse.ArgumentParser(prog="cad", description="Cdaprod CAD toolbox")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("backend", help="Show optional backend availability")
    p.set_defaults(func=cmd_backend)

    p = sub.add_parser("inspect", help="Inspect a model")
    p.add_argument("file")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("bounds", help="Print mesh bounding box")
    p.add_argument("file")
    p.set_defaults(func=cmd_bounds)

    p = sub.add_parser("convert", help="Convert model formats")
    p.add_argument("source")
    p.add_argument("destination")
    p.add_argument("--linear-deflection", type=float, default=0.1)
    p.set_defaults(func=cmd_convert)

    p = sub.add_parser("scale", help="Scale a mesh")
    p.add_argument("source")
    p.add_argument("destination")
    p.add_argument("--factor", required=True, type=float)
    p.set_defaults(func=cmd_scale)

    p = sub.add_parser("align", help="Align a mesh to origin")
    p.add_argument("source")
    p.add_argument("destination")
    p.add_argument("--center-x", action="store_true")
    p.add_argument("--center-y", action="store_true")
    p.add_argument("--center-xy", action="store_true")
    p.add_argument("--bottom-z", action="store_true")
    p.set_defaults(func=cmd_align)

    p = sub.add_parser("repair", help="Conservatively repair a mesh")
    p.add_argument("source")
    p.add_argument("destination")
    p.set_defaults(func=cmd_repair)

    p = sub.add_parser("boolean", help="BREP boolean on STEP files")
    p.add_argument("operation", choices=["cut", "fuse", "intersect"])
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("output")
    p.add_argument("--engine", choices=["build123d", "cadquery"], default="build123d")
    p.set_defaults(func=cmd_boolean)

    p = sub.add_parser("step-info", help="Basic STEP information")
    p.add_argument("file")
    p.set_defaults(func=cmd_step_info)

    make = sub.add_parser("make", help="Generate reusable geometry")
    make_sub = make.add_subparsers(dest="make_command", required=True)

    p = make_sub.add_parser("button-array")
    p.add_argument("output")
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--width", type=float, default=4.0)
    p.add_argument("--depth", type=float, default=6.0)
    p.add_argument("--height", type=float, default=2.5)
    p.add_argument("--spacing", type=float, default=12.0)
    p.set_defaults(func=cmd_make_button_array)

    p = make_sub.add_parser("port-cutter")
    p.add_argument("output")
    p.add_argument("--width", type=float, required=True)
    p.add_argument("--height", type=float, required=True)
    p.add_argument("--depth", type=float, required=True)
    p.add_argument("--clearance", type=float, default=0.30)
    p.add_argument("--corner-radius", type=float, default=0.0)
    p.set_defaults(func=cmd_make_port_cutter)

    return parser

def main():
    args = build_parser().parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
