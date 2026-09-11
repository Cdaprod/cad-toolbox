import argparse
from build123d import import_step

p = argparse.ArgumentParser()
p.add_argument("source")
args = p.parse_args()

shape = import_step(args.source)
bb = shape.bounding_box()
print({"min": [bb.min.X, bb.min.Y, bb.min.Z], "max": [bb.max.X, bb.max.Y, bb.max.Z],
       "size": [bb.size.X, bb.size.Y, bb.size.Z]})
