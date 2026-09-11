"""
Starter recipe because split placement is model-specific.

Edit SOURCE, OUTPUT_TOP, OUTPUT_BOTTOM and SPLIT_Z.
"""
from build123d import Plane, import_step, export_step

SOURCE = "enclosure.step"
OUTPUT_TOP = "enclosure-top.step"
OUTPUT_BOTTOM = "enclosure-bottom.step"
SPLIT_Z = 20.0

shape = import_step(SOURCE)
plane = Plane.XY.offset(SPLIT_Z)
parts = shape.split(bisect_by=plane)

# build123d split semantics can vary by shape; inspect returned objects before naming.
if isinstance(parts, (list, tuple)) and len(parts) >= 2:
    export_step(parts[0], OUTPUT_BOTTOM)
    export_step(parts[1], OUTPUT_TOP)
else:
    raise RuntimeError("Split did not return two parts; inspect the source solid and plane.")
