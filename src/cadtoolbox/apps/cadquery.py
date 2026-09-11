from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def load_step(path):
    try:
        import cadquery as cq
    except ImportError as exc:
        raise BackendUnavailable("CadQuery is not installed") from exc
    return cq.importers.importStep(str(path))

def save_step(shape, path):
    import cadquery as cq
    cq.exporters.export(shape, str(path))
    return Path(path)
