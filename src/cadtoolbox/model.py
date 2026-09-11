from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

BREP_SUFFIXES = {".step", ".stp", ".iges", ".igs", ".brep", ".fcstd"}
MESH_SUFFIXES = {".stl", ".obj", ".3mf", ".ply", ".glb", ".gltf"}
PROFILE_SUFFIXES = {".dxf", ".svg"}
SOURCE_SUFFIXES = {".py", ".scad"}

@dataclass(frozen=True)
class Model:
    path: Path
    units: str | None = None
    source_app: str | None = None

    @classmethod
    def from_path(cls, path: str | Path) -> "Model":
        return cls(Path(path).expanduser().resolve())

    @property
    def suffix(self) -> str:
        return self.path.suffix.lower()

    @property
    def kind(self) -> str:
        if self.suffix in BREP_SUFFIXES:
            return "brep"
        if self.suffix in MESH_SUFFIXES:
            return "mesh"
        if self.suffix in PROFILE_SUFFIXES:
            return "profile"
        if self.suffix in SOURCE_SUFFIXES:
            return "source"
        return "unknown"

    def require_exists(self) -> "Model":
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        return self
