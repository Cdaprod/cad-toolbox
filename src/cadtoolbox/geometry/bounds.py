def mesh_bounds(path):
    try:
        import trimesh
    except ImportError as exc:
        raise RuntimeError('Install mesh support: pip install -e ".[mesh]"') from exc
    obj = trimesh.load(path, force="scene")
    b = obj.bounds
    return {"min": b[0].tolist(), "max": b[1].tolist(),
            "size": (b[1] - b[0]).tolist()}
