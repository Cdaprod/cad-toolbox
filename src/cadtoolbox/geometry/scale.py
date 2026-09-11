from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def scale_mesh(source: str | Path, destination: str | Path, factor: float) -> Path:
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    source, destination = Path(source), Path(destination)
    obj = trimesh.load(source, force="scene")
    obj.apply_scale(float(factor))
    obj.export(destination)
    return destination
