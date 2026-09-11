from __future__ import annotations
import importlib.util
import shutil

def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None

def executable_available(name: str) -> bool:
    return shutil.which(name) is not None

def backend_status() -> dict[str, bool]:
    return {
        "trimesh": module_available("trimesh"),
        "build123d": module_available("build123d"),
        "cadquery": module_available("cadquery"),
        "FreeCAD": module_available("FreeCAD"),
        "bpy": module_available("bpy"),
        "openscad": executable_available("openscad"),
    }
