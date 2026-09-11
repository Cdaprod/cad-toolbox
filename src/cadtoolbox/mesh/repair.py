from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def repair_mesh(source: str | Path, destination: str | Path) -> dict:
    """
    Conservative mesh repair.

    Operations:
    - merge duplicate vertices
    - remove unreferenced vertices
    - remove infinite/NaN values
    - fix normals
    - fill simple holes when trimesh can
    """
    try:
        import trimesh
    except ImportError as exc:
        raise BackendUnavailable('Install mesh support: pip install -e ".[mesh]"') from exc

    source, destination = Path(source), Path(destination)
    scene = trimesh.load(source, force="scene")
    mesh = scene.to_mesh()

    before = {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
    }

    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.fix_normals(multibody=True)

    try:
        trimesh.repair.fill_holes(mesh)
    except Exception:
        pass

    mesh.export(destination)

    after = {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
    }
    return {"before": before, "after": after, "output": str(destination)}
