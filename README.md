# cad-toolbox

Cross-application CAD/geometry operations toolbox organized **operation first,
application second**.

Use it for on-the-fly geometry and file operations from CLI, FreeCAD, Blender,
build123d, CadQuery and OpenSCAD.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[mesh,build123d,cadquery,dev]"
cad --help
cad inspect path/to/model.step
cad bounds path/to/model.stl
```

## Organization

- `src/cadtoolbox/` reusable functionality
- `scripts/<app>/` code intended to run specifically inside an application
- `recipes/` repeatable workflows that have not become library features
- `examples/` small working examples
- `assets/fixtures/` tiny test/reference fixtures only

Keep your actual project models and bulk downloads in your separate 3D-model
repository. This repo is the tooling layer.
