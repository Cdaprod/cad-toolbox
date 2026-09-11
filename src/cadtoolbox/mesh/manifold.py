from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def inspect_manifold(path: str | Path) -> dict:
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    mesh = trimesh.load(Path(path), force="scene").to_mesh()
    return {
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "body_count": int(mesh.body_count),
    }
