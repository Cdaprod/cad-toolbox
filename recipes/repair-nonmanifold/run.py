import argparse
from cadtoolbox.mesh.repair import repair_mesh
from cadtoolbox.mesh.manifold import inspect_manifold

p = argparse.ArgumentParser()
p.add_argument("source")
p.add_argument("output")
args = p.parse_args()
print(repair_mesh(args.source, args.output))
print(inspect_manifold(args.output))
