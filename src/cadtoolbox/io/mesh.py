from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def convert_mesh(source: str | Path, destination: str | Path) -> Path:
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    source, destination = Path(source), Path(destination)
    obj = trimesh.load(source, force="scene")
    obj.export(destination)
    return destination
