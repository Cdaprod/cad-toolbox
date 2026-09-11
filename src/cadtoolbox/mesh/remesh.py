from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def subdivide_mesh(source: str | Path, destination: str | Path, iterations: int = 1) -> Path:
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    mesh = trimesh.load(Path(source), force="scene").to_mesh()
    for _ in range(int(iterations)):
        mesh = mesh.subdivide()
    mesh.export(Path(destination))
    return Path(destination)
