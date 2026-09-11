from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def align_mesh(
    source: str | Path,
    destination: str | Path,
    *,
    center_x: bool = False,
    center_y: bool = False,
    center_xy: bool = False,
    bottom_z: bool = False,
) -> Path:
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    source, destination = Path(source), Path(destination)
    obj = trimesh.load(source, force="scene")
    bounds = obj.bounds
    center = (bounds[0] + bounds[1]) / 2.0

    tx = -center[0] if (center_x or center_xy) else 0.0
    ty = -center[1] if (center_y or center_xy) else 0.0
    tz = -bounds[0][2] if bottom_z else 0.0

    obj.apply_translation([tx, ty, tz])
    obj.export(destination)
    return destination
