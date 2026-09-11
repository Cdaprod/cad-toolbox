"""
Run inside Blender:
    blender --python scripts/blender/inspect_and_center.py -- /path/model.stl
"""
import sys
from pathlib import Path

from cadtoolbox.apps.blender import clear_scene, import_stl

def argv_after_double_dash():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

args = argv_after_double_dash()
if not args:
    raise SystemExit("usage: blender --python inspect_and_center.py -- model.stl")

path = Path(args[0]).expanduser().resolve()
clear_scene()
objects = import_stl(path)

import bpy
for obj in objects:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    obj.location.x = 0
    obj.location.y = 0

print(f"Imported and XY-centered: {path}")
