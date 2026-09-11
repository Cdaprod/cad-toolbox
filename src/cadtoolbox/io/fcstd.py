from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def open_freecad_document(path: str | Path):
    try:
        import FreeCAD
    except ImportError as exc:
        raise BackendUnavailable("Run inside FreeCAD Python or install FreeCAD's Python environment.") from exc
    return FreeCAD.openDocument(str(path))
