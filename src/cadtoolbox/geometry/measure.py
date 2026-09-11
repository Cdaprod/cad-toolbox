from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def mesh_measurements(path: str | Path) -> dict:
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    obj = trimesh.load(Path(path), force="scene")
    mesh = obj.to_mesh()
    result = {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "area": float(mesh.area),
    }
    try:
        result["volume"] = float(mesh.volume)
    except Exception:
        result["volume"] = None
    return result
