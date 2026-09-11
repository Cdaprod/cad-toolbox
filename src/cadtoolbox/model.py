from dataclasses import dataclass
from pathlib import Path

BREP_SUFFIXES = {".step", ".stp", ".iges", ".igs", ".brep", ".fcstd"}
MESH_SUFFIXES = {".stl", ".obj", ".3mf", ".ply", ".glb"}
PROFILE_SUFFIXES = {".dxf", ".svg"}

@dataclass(frozen=True)
class Model:
    path: Path
    units: str | None = None
    source_app: str | None = None

    @classmethod
    def from_path(cls, path):
        return cls(Path(path).expanduser().resolve())

    @property
    def suffix(self):
        return self.path.suffix.lower()

    @property
    def kind(self):
        if self.suffix in BREP_SUFFIXES:
            return "brep"
        if self.suffix in MESH_SUFFIXES:
            return "mesh"
        if self.suffix in PROFILE_SUFFIXES:
            return "profile"
        return "unknown"
