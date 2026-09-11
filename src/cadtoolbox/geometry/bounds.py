from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def mesh_bounds(path: str | Path) -> dict:
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    scene = trimesh.load(Path(path), force="scene")
    bounds = scene.bounds
    return {
        "min": [float(v) for v in bounds[0]],
        "max": [float(v) for v in bounds[1]],
        "size": [float(v) for v in (bounds[1] - bounds[0])],
    }
