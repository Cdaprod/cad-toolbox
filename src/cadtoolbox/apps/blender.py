from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def _bpy():
    try:
        import bpy
    except ImportError as exc:
        raise BackendUnavailable("This adapter must run inside Blender Python.") from exc
    return bpy

def clear_scene():
    bpy = _bpy()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

def import_stl(path):
    bpy = _bpy()
    path = str(Path(path))
    # Blender 4.x operator first; older fallback second.
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        bpy.ops.import_mesh.stl(filepath=path)
    return list(bpy.context.selected_objects)

def export_stl(path, selection_only=False):
    bpy = _bpy()
    path = str(Path(path))
    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=selection_only)
    else:
        bpy.ops.export_mesh.stl(filepath=path, use_selection=selection_only)
    return Path(path)
