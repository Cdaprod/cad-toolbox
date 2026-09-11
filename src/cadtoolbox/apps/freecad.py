from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def _modules():
    try:
        import FreeCAD
        import Part
    except ImportError as exc:
        raise BackendUnavailable("This adapter must run in a FreeCAD Python environment.") from exc
    return FreeCAD, Part

def new_document(name="cadtoolbox"):
    FreeCAD, _ = _modules()
    return FreeCAD.newDocument(name)

def import_step(path, document=None, label=None):
    FreeCAD, Part = _modules()
    doc = document or FreeCAD.ActiveDocument or FreeCAD.newDocument("cadtoolbox")
    shape = Part.read(str(path))
    obj = doc.addObject("PartDesign::Feature", label or Path(path).stem)
    obj.Shape = shape
    doc.recompute()
    return obj

def save_as_step(obj, path):
    _, Part = _modules()
    Part.export([obj], str(path))
    return Path(path)
