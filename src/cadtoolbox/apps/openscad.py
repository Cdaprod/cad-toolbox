from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
from cadtoolbox.errors import BackendUnavailable

def run_openscad(source: str | Path, output: str | Path, *, defines: dict | None = None) -> Path:
    exe = shutil.which("openscad")
    if not exe:
        raise BackendUnavailable("OpenSCAD CLI was not found on PATH.")

    cmd = [exe, "-o", str(output)]
    for key, value in (defines or {}).items():
        if isinstance(value, str):
            expr = f'{key}="{value}"'
        elif isinstance(value, bool):
            expr = f"{key}={'true' if value else 'false'}"
        else:
            expr = f"{key}={value}"
        cmd += ["-D", expr]
    cmd.append(str(source))
    subprocess.run(cmd, check=True)
    return Path(output)
