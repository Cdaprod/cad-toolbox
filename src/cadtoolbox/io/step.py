from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def import_build123d(path: str | Path):
    try:
        from build123d import import_step
    except ImportError as exc:
        raise BackendUnavailable('Install build123d: pip install -e ".[build123d]"') from exc
    return import_step(str(path))

def export_build123d(shape, path: str | Path):
    try:
        from build123d import export_step
    except ImportError as exc:
        raise BackendUnavailable('Install build123d: pip install -e ".[build123d]"') from exc
    export_step(shape, str(path))
    return Path(path)

def import_cadquery(path: str | Path):
    try:
        import cadquery as cq
    except ImportError as exc:
        raise BackendUnavailable('Install CadQuery: pip install -e ".[cadquery]"') from exc
    return cq.importers.importStep(str(path))

def export_cadquery(shape, path: str | Path):
    try:
        import cadquery as cq
    except ImportError as exc:
        raise BackendUnavailable('Install CadQuery: pip install -e ".[cadquery]"') from exc
    cq.exporters.export(shape, str(path))
    return Path(path)
