from __future__ import annotations
from pathlib import Path
from cadtoolbox.model import Model
from cadtoolbox.errors import UnsupportedFormat
from cadtoolbox.io.mesh import convert_mesh

def convert(source: str | Path, destination: str | Path, *, linear_deflection: float = 0.1) -> Path:
    src, dst = Model.from_path(source).require_exists(), Model.from_path(destination)

    if src.kind == "mesh" and dst.kind == "mesh":
        return convert_mesh(src.path, dst.path)

    if src.kind == "brep" and src.suffix in {".step", ".stp"} and dst.kind == "mesh":
        try:
            from build123d import import_step, export_stl
        except ImportError as exc:
            raise RuntimeError(
                'STEP → mesh conversion requires build123d: pip install -e ".[build123d]"'
            ) from exc
        shape = import_step(str(src.path))
        # build123d controls tessellation internally; keep argument in API for future tuning.
        export_stl(shape, str(dst.path))
        return dst.path

    raise UnsupportedFormat(f"unsupported conversion: {src.suffix} -> {dst.suffix}")
