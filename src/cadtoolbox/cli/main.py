import argparse
from cadtoolbox.model import Model
from cadtoolbox.geometry.bounds import mesh_bounds

def inspect(args):
    m = Model.from_path(args.file)
    if not m.path.exists():
        raise SystemExit(f"not found: {m.path}")
    print(f"path:   {m.path}")
    print(f"format: {m.suffix or '(none)'}")
    print(f"kind:   {m.kind}")
    print(f"bytes:  {m.path.stat().st_size:,}")

def bounds(args):
    m = Model.from_path(args.file)
    if m.kind != "mesh":
        raise SystemExit("bounds currently supports mesh formats via trimesh")
    b = mesh_bounds(m.path)
    print(f"min:  {b['min']}")
    print(f"max:  {b['max']}")
    print(f"size: {b['size']}")

def main():
    parser = argparse.ArgumentParser(prog="cad", description="Cdaprod CAD toolbox")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect")
    p.add_argument("file")
    p.set_defaults(func=inspect)
    p = sub.add_parser("bounds")
    p.add_argument("file")
    p.set_defaults(func=bounds)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
