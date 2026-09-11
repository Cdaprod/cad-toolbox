import argparse
from build123d import export_step
from cadtoolbox.cutters.port import PortSpec, build123d_port_cutter

p = argparse.ArgumentParser()
p.add_argument("output")
p.add_argument("--width", type=float, required=True)
p.add_argument("--height", type=float, required=True)
p.add_argument("--depth", type=float, required=True)
p.add_argument("--clearance", type=float, default=0.30)
args = p.parse_args()

shape = build123d_port_cutter(PortSpec(args.width, args.height, args.depth, args.clearance))
export_step(shape, args.output)
print(args.output)
