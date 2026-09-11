from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def decimate_mesh(source: str | Path, destination: str | Path, faces: int) -> Path:
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    mesh = trimesh.load(Path(source), force="scene").to_mesh()
    simplified = mesh.simplify_quadric_decimation(face_count=int(faces))
    simplified.export(Path(destination))
    return Path(destination)
