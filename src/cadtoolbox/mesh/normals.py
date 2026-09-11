from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def fix_normals(source: str | Path, destination: str | Path) -> Path:
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    mesh = trimesh.load(Path(source), force="scene").to_mesh()
    mesh.fix_normals(multibody=True)
    mesh.export(Path(destination))
    return Path(destination)
