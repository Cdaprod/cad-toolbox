import argparse
from pathlib import Path
from cadtoolbox.mesh.repair import repair_mesh

p = argparse.ArgumentParser()
p.add_argument("source")
p.add_argument("output")
args = p.parse_args()

result = repair_mesh(args.source, args.output)
print(result)
print("Next: import the repaired mesh into FreeCAD/Blender and reconstruct a BREP.")
