import argparse
from cadtoolbox.geometry.align import align_mesh

p = argparse.ArgumentParser()
p.add_argument("source")
p.add_argument("output")
args = p.parse_args()
print(align_mesh(args.source, args.output, center_xy=True, bottom_z=True))
