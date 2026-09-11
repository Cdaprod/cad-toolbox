# cad-toolbox

Cross-application CAD/geometry toolbox for command-line, build123d, CadQuery,
FreeCAD, Blender, OpenSCAD and mesh workflows.

The repo is organized **operation first, application second**.

## What is implemented

### CLI
- `cad inspect`
- `cad bounds`
- `cad convert`
- `cad scale`
- `cad align`
- `cad repair`
- `cad boolean`
- `cad step-info`
- `cad backend`
- `cad make button-array`
- `cad make port-cutter`

### Backends
- `trimesh` for mesh inspection, repair, conversion, alignment and scaling
- `build123d` for STEP import/export and BREP booleans
- `CadQuery` adapter for STEP import/export and BREP booleans
- Blender adapter callable from Blender Python
- FreeCAD adapter callable from FreeCAD Python
- OpenSCAD runner adapter

### Reusable geometry
- units
- transforms
- bounds
- alignment
- scaling
- mesh repair / normals / manifold inspection
- BREP booleans
- button/port/fastener cutters
- reference envelopes and placement helpers

### Recipes
- Doesbot CNC enclosure in build123d
- STEP → STL
- mesh → repaired mesh
- align model to origin
- create port cutter
- split enclosure starter

## Install

Recommended on macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[all]"
```

If `cadquery` and `build123d` conflict in a specific environment, install the
core + one CAD backend first:

```bash
python -m pip install -e ".[mesh,build123d,dev]"
```

or:

```bash
python -m pip install -e ".[mesh,cadquery,dev]"
```

## Examples

```bash
cad inspect model.step
cad bounds model.stl
cad repair bad.stl repaired.stl
cad align model.stl aligned.stl --center-xy --bottom-z
cad scale inch-part.stl mm-part.stl --factor 25.4
cad convert part.stl part.obj
cad convert part.step part.stl --linear-deflection 0.15
cad boolean cut enclosure.step cutter.step enclosure-cut.step --engine build123d
cad make button-array buttons.step --count 3 --width 4 --depth 6 --height 2.5 --spacing 12
cad make port-cutter hdmi-cutter.step --width 15 --height 7 --depth 12 --clearance 0.35
```

## Repo rule

If functionality is reusable outside one application, it belongs under
`src/cadtoolbox/`.

If it must execute inside Blender or FreeCAD, use `scripts/<app>/`.

If it is a specific solved workflow, use `recipes/<workflow>/`.

## Working models vs tooling

Do not turn this repository into a dump of downloaded STEP/STL files. Keep
project models in your separate 3D-model repository. This repo should stay
small enough to clone quickly from your MacBook or iPhone.
