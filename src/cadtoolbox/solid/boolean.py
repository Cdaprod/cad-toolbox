from __future__ import annotations
from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def boolean_step(
    operation: str,
    a_path: str | Path,
    b_path: str | Path,
    output_path: str | Path,
    *,
    engine: str = "build123d",
) -> Path:
    operation = operation.lower()
    if operation not in {"cut", "fuse", "intersect"}:
        raise ValueError("operation must be cut, fuse, or intersect")

    if engine == "build123d":
        try:
            from build123d import import_step, export_step
        except ImportError as exc:
            raise BackendUnavailable('Install build123d: pip install -e ".[build123d]"') from exc
        a, b = import_step(str(a_path)), import_step(str(b_path))
        result = {"cut": lambda: a - b, "fuse": lambda: a + b, "intersect": lambda: a & b}[operation]()
        export_step(result, str(output_path))
        return Path(output_path)

    if engine == "cadquery":
        try:
            import cadquery as cq
        except ImportError as exc:
            raise BackendUnavailable('Install CadQuery: pip install -e ".[cadquery]"') from exc
        a, b = cq.importers.importStep(str(a_path)), cq.importers.importStep(str(b_path))
        if operation == "cut":
            result = a.cut(b)
        elif operation == "fuse":
            result = a.union(b)
        else:
            result = a.intersect(b)
        cq.exporters.export(result, str(output_path))
        return Path(output_path)

    raise ValueError(f"unknown engine: {engine}")
