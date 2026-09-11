# Voronoi Lattice — Trimesh / SciPy

Generate Voronoi-based lattice geometry from arbitrary 3D meshes using:

- `trimesh`
- `scipy.spatial.Voronoi`
- `numpy`
- `rtree`
- `manifold3d`

This recipe supports two distinct workflows:

1. **Volumetric Voronoi lattice**
   - samples points inside a closed solid
   - builds a true 3D Voronoi diagram
   - converts Voronoi edges into cylindrical struts
   - unions the struts
   - clips the final lattice to the source model

2. **Surface Voronoi modifier**
   - distributes seeds over the mesh surface
   - assigns surface triangles to the nearest seed
   - extracts boundaries between Voronoi regions
   - converts those boundaries into surface-following struts
   - can be restricted to selected regions of the model

The script also includes built-in demo geometry so the algorithm can be tested without supplying a model.

—

## Files

```text
trimesh/
├── README.md
└── voronoi_lattice.py
```

Primary entrypoint:

```bash
python3 voronoi_lattice.py
```

—

# Installation

Recommended Python environment:

```bash
python3 -m pip install \
  numpy \
  scipy \
  trimesh \
  rtree \
  manifold3d \
  pyglet
```

Minimum core dependencies:

```text
numpy
scipy
trimesh
rtree
manifold3d
```

`manifold3d` is required for robust boolean union/intersection in printable volumetric mode.

—

# Quick Start

## Run the built-in demo

No arguments are required.

```bash
python3 voronoi_lattice.py
```

This generates the default sphere demo using the surface Voronoi mode.

Equivalent to:

```bash
python3 voronoi_lattice.py \
  —demo sphere \
  —mode surface
```

—

# Original Simple Workflow

The original usage remains available.

```bash
python3 voronoi_lattice.py path/to/model.stl
```

For compatibility, an explicitly supplied model defaults to the original volumetric lattice workflow.

Equivalent to:

```bash
python3 voronoi_lattice.py \
  path/to/model.stl \
  —mode volume
```

Example:

```bash
python3 voronoi_lattice.py enclosure.stl
```

—

# Modes

## Volume Mode

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode volume
```

Pipeline:

```text
source solid
    │
    ▼
sample interior seed points
    │
    ▼
SciPy 3D Voronoi
    │
    ▼
extract finite Voronoi ridge edges
    │
    ▼
cylindrical struts + spherical nodes
    │
    ▼
boolean union
    │
    ▼
intersection with source model
    │
    ▼
printable Voronoi lattice
```

Volume mode is appropriate when the goal is to replace or fill the interior of a solid with an organic lattice.

The source should be:

```text
closed
watertight
manifold
```

—

## Surface Mode

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface
```

Surface mode creates a Voronoi-like network that follows the actual exterior geometry of the model.

Pipeline:

```text
source mesh
    │
    ▼
optional subdivision
    │
    ▼
sample surface seeds
    │
    ▼
assign each triangle to nearest seed
    │
    ▼
find boundaries between neighboring regions
    │
    ▼
convert boundaries into struts
    │
    ▼
surface-following Voronoi network
```

This is useful for:

- camera grips
- enclosure side panels
- decorative shells
- handles
- curved housings
- organic surface patterns
- lightweight visual structures

Unlike a simple XY projection, this method follows the arbitrary 3D mesh surface.

—

# Built-In Demo Geometry

Available demo models:

```text
sphere
cube
cylinder
panel
```

## Sphere

```bash
python3 voronoi_lattice.py \
  —demo sphere
```

Best for testing:

- curved topology
- arbitrary surface following
- organic patterns
- distortion behavior

—

## Cube

```bash
python3 voronoi_lattice.py \
  —demo cube
```

Best for testing:

- hard edges
- face transitions
- corner behavior
- planar surfaces

—

## Cylinder

```bash
python3 voronoi_lattice.py \
  —demo cylinder
```

Best for approximating:

- grips
- tubes
- handles
- camera rig parts
- cylindrical housings

—

## Panel

```bash
python3 voronoi_lattice.py \
  —demo panel
```

Best for:

- enclosure walls
- projected-pattern experiments
- decorative panels
- flat or nearly flat surfaces

—

# Generate All Demo Models

```bash
python3 voronoi_lattice.py \
  —demo all
```

Typical output:

```text
exports/
└── voronoi-lattice/
    ├── sphere/
    │   ├── sphere-voronoi-surface.stl
    │   ├── sphere-voronoi-surface.glb
    │   └── sphere-voronoi-surface.json
    │
    ├── cube/
    │   ├── cube-voronoi-surface.stl
    │   ├── cube-voronoi-surface.glb
    │   └── cube-voronoi-surface.json
    │
    ├── cylinder/
    │   ├── cylinder-voronoi-surface.stl
    │   ├── cylinder-voronoi-surface.glb
    │   └── cylinder-voronoi-surface.json
    │
    └── panel/
        ├── panel-voronoi-surface.stl
        ├── panel-voronoi-surface.glb
        └── panel-voronoi-surface.json
```

`—demo all` is useful as a basic visual regression test after modifying the algorithm.

—

# Common Parameters

## Seed Count

```bash
—seeds 85
```

Controls Voronoi density.

Fewer seeds:

```text
larger cells
fewer struts
more open geometry
```

More seeds:

```text
smaller cells
denser lattice
more geometry
slower processing
```

Example:

```bash
python3 voronoi_lattice.py \
  —demo sphere \
  —seeds 45
```

Guardrail:

```text
12 .. 400
```

—

# Strut Radius

```bash
—strut-radius 1.2
```

Example:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —strut-radius 1.5
```

If omitted, the value is automatically scaled relative to the model size.

—

# Node Size

```bash
—node-scale 1.12
```

Controls the radius of node spheres relative to the struts.

```text
node radius =
strut radius × node scale
```

To disable node spheres entirely:

```bash
—no-nodes
```

Example:

```bash
python3 voronoi_lattice.py \
  —demo sphere \
  —no-nodes
```

—

# Quality

Available levels:

```text
low
medium
high
```

Example:

```bash
python3 voronoi_lattice.py \
  —demo sphere \
  —quality high
```

Higher quality increases cylinder segmentation and node tessellation.

Use `medium` during development.

Use `high` for final exports.

—

# Deterministic Patterns

The generator is deterministic when using the same random seed.

Default:

```bash
—random-seed 42
```

Changing the seed produces a new pattern:

```bash
python3 voronoi_lattice.py \
  —demo sphere \
  —random-seed 123
```

This makes it possible to regenerate the same pattern later.

—

# Surface Selection

Surface mode can restrict the Voronoi modifier to selected areas.

Supported selection methods:

```text
box region
sphere region
brush-stroke JSON
```

Multiple selection regions are unioned together.

—

# Box Selection

Syntax:

```bash
—select-box \
  XMIN YMIN ZMIN \
  XMAX YMAX ZMAX
```

Example:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —select-box \
  -30 -30 0 \
   30  30 50
```

Multiple boxes can be supplied:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —select-box -30 -30 0 30 30 50 \
  —select-box 40 -20 10 70 20 40
```

—

# Sphere Selection

Syntax:

```bash
—select-sphere X Y Z RADIUS
```

Example:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —select-sphere 20 0 30 25
```

This is useful for quickly placing a Voronoi patch on a grip or enclosure.

—

# Invert Selection

Apply the modifier everywhere except the selected region:

```bash
—invert-selection
```

Example:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —select-sphere 0 0 30 20 \
  —invert-selection
```

—

# Selection Margin

Expand selection boundaries without redefining the region:

```bash
—selection-margin 2
```

Example:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —select-sphere 20 0 30 25 \
  —selection-margin 2
```

—

# Selection Cleanup

Selections are mapped onto mesh faces.

To prevent small holes or missed triangles, surface selections can be expanded or eroded using face adjacency.

## Dilate

```bash
—selection-dilate 2
```

Expands the selected region outward across neighboring triangles.

Useful for:

```text
closing tiny gaps
cleaning brush selections
avoiding isolated unselected faces
```

—

## Erode

```bash
—selection-erode 1
```

Shrinks the selected region inward.

Useful for:

```text
creating clearance from edges
removing marginal selections
cleaning noisy borders
```

—

# Selection Preview

Before generating the lattice, export a GLB showing the affected region:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —select-sphere 20 0 30 25 \
  —selection-preview
```

Output:

```text
model-selection-preview.glb
```

Selected faces are highlighted.

This creates a fast workflow:

```text
define region
    │
    ▼
selection preview
    │
    ▼
inspect GLB
    │
    ▼
adjust selection
    │
    ▼
generate Voronoi geometry
```

—

# Brush Selection

More complex arbitrary regions can be defined using brush strokes.

Example JSON:

```json
{
  “strokes”: [
    {
      “radius”: 12.0,
      “points”: [
        [14, -5, 20],
        [17, -4, 28],
        [20, -2, 36],
        [22, 1, 44],
        [23, 5, 52]
      ]
    }
  ]
}
```

Save as:

```text
selection.json
```

Then run:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —selection-file selection.json
```

Brush strokes are treated as chains of spherical selection samples.

This format is intentionally frontend-independent.

A future UI can generate the same JSON from:

```text
browser raycasting
Blender
FreeCAD
touchscreen
iPhone browser
desktop mouse
```

without changing the geometry engine.

—

# Preview Brush Selection

Recommended workflow:

```bash
python3 voronoi_lattice.py \
  grip.stl \
  —mode surface \
  —selection-file grip-side.json \
  —selection-dilate 2 \
  —selection-preview
```

Then generate:

```bash
python3 voronoi_lattice.py \
  grip.stl \
  —mode surface \
  —selection-file grip-side.json \
  —selection-dilate 2 \
  —seeds 90 \
  —quality high
```

—

# Volume Selection

Selections can also restrict volume-mode struts.

Example:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode volume \
  —select-sphere 0 0 30 25
```

Volume struts can be tested against the selection using:

```bash
—segment-selection midpoint
```

or:

```bash
—segment-selection touch
```

or:

```bash
—segment-selection inside
```

Meaning:

```text
midpoint
    Keep the strut if its midpoint is selected.

touch
    Keep the strut if either endpoint or midpoint enters the selection.

inside
    Keep the strut only if both endpoints and midpoint are selected.
```

Default:

```text
midpoint
```

—

# Surface Selection Edge Behavior

Surface Voronoi boundaries exist between neighboring triangles.

The selection system determines whether those boundary edges should survive.

Default:

```bash
—surface-selection-edge both
```

Both adjacent faces must be selected.

Alternative:

```bash
—surface-selection-edge either
```

The edge survives if either neighboring face is selected.

`both` generally produces cleaner clipped patterns.

—

# Surface Resolution

Surface mode relies on the source mesh triangles to approximate Voronoi region boundaries.

Very coarse meshes are automatically subdivided.

Control the target edge length:

```bash
—surface-max-edge 2.5
```

Example:

```bash
python3 voronoi_lattice.py \
  grip.stl \
  —mode surface \
  —surface-max-edge 2.0
```

Smaller values:

```text
better boundary resolution
more triangles
more memory
slower processing
```

A safety ceiling is also available:

```bash
—surface-max-faces 60000
```

—

# Volume Guard Points

Volume mode uses a sparse box of helper points surrounding the source mesh to encourage finite Voronoi cells.

Control the margin:

```bash
—guard-margin 20
```

Control helper density:

```bash
—guard-grid 3
```

Normally these values can remain automatic.

—

# Maximum Struts

To prevent accidental geometry explosions:

```bash
—max-struts 1800
```

Guardrail:

```text
100 .. 5000
```

If more struts are generated, a deterministic subset is retained.

—

# Preview-Only Mode

Skip expensive boolean operations:

```bash
—preview-only
```

Example:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode volume \
  —preview-only
```

Useful while tuning:

```text
seed count
random seed
strut thickness
selection regions
pattern density
```

Preview mode can contain:

```text
overlapping struts
unmerged nodes
geometry outside the source volume
```

It should not automatically be considered printable.

—

# Repair

Attempt basic mesh repair:

```bash
—repair
```

Example:

```bash
python3 voronoi_lattice.py \
  damaged.stl \
  —mode volume \
  —repair
```

Repair currently attempts:

```text
normal correction
hole filling
unused vertex removal
```

This is intentionally conservative.

Severely broken meshes should be repaired externally.

—

# Output

Each completed run produces:

```text
STL
GLB
JSON manifest
```

Example:

```text
camera-grip-voronoi-surface.stl
camera-grip-voronoi-surface.glb
camera-grip-voronoi-surface.json
```

The JSON manifest records the effective configuration used to generate the output.

Example information:

```json
{
  “mode”: “surface”,
  “seeds”: 85,
  “strut_radius_mm”: 1.15,
  “node_radius_mm”: 1.288,
  “quality”: “medium”,
  “random_seed”: 42,
  “selection_enabled”: true,
  “source_extents_mm”: [
    60.0,
    35.0,
    100.0
  ]
}
```

Output names are stable.

Running the same source again with different parameters replaces the corresponding generated files.

—

# Custom Output Directory

```bash
python3 voronoi_lattice.py \
  model.stl \
  —output-dir ./build/voronoi
```

—

# Custom Output Name

```bash
python3 voronoi_lattice.py \
  model.stl \
  —output-name grip-organic
```

Example output:

```text
grip-organic-voronoi-volume.stl
grip-organic-voronoi-volume.glb
grip-organic-voronoi-volume.json
```

—

# Practical Examples

## Fast sphere experiment

```bash
python3 voronoi_lattice.py
```

—

## Organic sphere surface

```bash
python3 voronoi_lattice.py \
  —demo sphere \
  —mode surface \
  —seeds 55 \
  —strut-radius 1.2
```

—

## Dense sphere

```bash
python3 voronoi_lattice.py \
  —demo sphere \
  —mode surface \
  —seeds 140 \
  —strut-radius 0.8 \
  —quality high
```

—

## True internal sphere lattice

```bash
python3 voronoi_lattice.py \
  —demo sphere \
  —mode volume \
  —seeds 65 \
  —strut-radius 1.2
```

—

## Voronoi camera grip surface

```bash
python3 voronoi_lattice.py \
  camera-grip.stl \
  —mode surface \
  —seeds 110 \
  —strut-radius 1.0 \
  —quality high
```

—

## Only modify one side of a grip

```bash
python3 voronoi_lattice.py \
  camera-grip.stl \
  —mode surface \
  —select-sphere 25 0 40 35 \
  —selection-dilate 2 \
  —selection-preview
```

After checking the preview:

```bash
python3 voronoi_lattice.py \
  camera-grip.stl \
  —mode surface \
  —select-sphere 25 0 40 35 \
  —selection-dilate 2 \
  —seeds 100 \
  —quality high
```

—

## Preserve port regions

Select the port area and invert the selection:

```bash
python3 voronoi_lattice.py \
  enclosure.stl \
  —mode surface \
  —select-box \
  20 -15 5 \
  50  15 30 \
  —invert-selection
```

The Voronoi network is generated everywhere except the protected box.

—

# Choosing Between Surface and Volume

Use:

```text
surface
```

when the desired result is:

```text
decorative
wrapped
skin-like
organic
surface-following
selectively applied
```

Use:

```text
volume
```

when the desired result is:

```text
structural interior
true 3D cellular lattice
open internal framework
solid replacement
volume-filling
```

A useful mental model:

```text
SURFACE

original object
      +
Voronoi network on its skin


VOLUME

original object’s volume
      replaced/clipped by
3D Voronoi strut network
```

—

# Recommended Development Workflow

During experimentation:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —selection-preview
```

Then:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —preview-only \
  —quality low
```

Then final:

```bash
python3 voronoi_lattice.py \
  model.stl \
  —mode surface \
  —quality high
```

For volume mode:

```text
preview-only
    ↓
verify pattern
    ↓
printable boolean build
    ↓
inspect watertight result
```

—

# CLI Help

Always use the script itself as the authoritative parameter reference:

```bash
python3 voronoi_lattice.py —help
```

—

# Current Architecture

```text
                    voronoi_lattice.py
                           │
           ┌───────────────┴───────────────┐
           │                               │
       INPUT FILE                       DEMO
           │                               │
           └───────────────┬───────────────┘
                           │
                           ▼
                     Trimesh model
                           │
             ┌─────────────┴─────────────┐
             │                           │
          volume                       surface
             │                           │
      interior sampling           surface sampling
             │                           │
      SciPy Voronoi              nearest-site regions
             │                           │
       ridge edges                region boundaries
             │                           │
             └─────────────┬─────────────┘
                           │
                       selection
                           │
                     cleanup/mask
                           │
                      strut builder
                           │
                       nodes
                           │
             ┌─────────────┴─────────────┐
             │                           │
         boolean clip                surface union
             │                           │
             └─────────────┬─────────────┘
                           │
                           ▼
                    STL / GLB / JSON
```

—

# Future Extensions

The current selection backend is intentionally designed so future frontends can be added without rewriting the geometry engine.

Planned/possible additions:

```text
interactive browser brush painter
Three.js mesh raycasting
live GLB preview
selection erase brush
selection layers
protected regions
face-group selection
normal-angle selection
curvature-based selection
distance-from-edge masks
geodesic brush distance
adaptive Voronoi density
weighted seeds
Lloyd relaxation
surface inset/cut modes
solid-shell preservation
Boolean perforation mode
FreeCAD integration
Blender integration
build123d wrapper
STEP/BREP output pipeline
```

A browser frontend could eventually follow:

```text
load model
    │
    ▼
rotate / inspect
    │
    ▼
paint area
    │
    ▼
raycast brush → XYZ samples
    │
    ▼
selection JSON
    │
    ▼
voronoi_lattice.py
    │
    ▼
preview
    │
    ▼
final export
```

That keeps the CLI recipe usable independently while allowing progressively richer tooling around it.

—

# Design Goal

This recipe is intended to remain:

```text
simple enough for one-command use
        +
parameterized enough for CAD experimentation
        +
guardrailed enough to avoid obviously destructive settings
        +
modular enough to become an interactive modifier later
```

The simplest supported invocation should continue to remain:

```bash
python3 voronoi_lattice.py model.stl
```

while advanced workflows remain available through explicit CLI options.