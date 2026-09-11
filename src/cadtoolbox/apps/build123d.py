from pathlib import Path
from cadtoolbox.errors import BackendUnavailable

def load_step(path):
    try:
        from build123d import import_step
    except ImportError as exc:
        raise BackendUnavailable("build123d is not installed") from exc
    return import_step(str(path))

def save_step(shape, path):
    from build123d import export_step
    export_step(shape, str(path))
    return Path(path)

def save_stl(shape, path):
    from build123d import export_stl
    export_stl(shape, str(path))
    return Path(path)
