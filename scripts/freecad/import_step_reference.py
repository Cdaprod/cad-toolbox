"""
Run from FreeCAD's Python console with exec(open(...).read()) after setting MODEL,
or use FreeCADCmd with a small wrapper.

Example:
    MODEL="/tmp/board.step"
    exec(open("scripts/freecad/import_step_reference.py").read())
"""
from pathlib import Path
from cadtoolbox.apps.freecad import import_step

if "MODEL" not in globals():
    raise RuntimeError("Set MODEL to a STEP file path before running.")

obj = import_step(Path(MODEL), label=Path(MODEL).stem)
print(f"Imported reference: {obj.Label}")
