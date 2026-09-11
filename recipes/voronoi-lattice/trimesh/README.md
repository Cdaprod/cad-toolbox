# Voronoi Lattice Recipe

Turns a closed mesh solid into a 3D Voronoi strut lattice and exports a stable
STL + GLB pair suitable for printing and browser inspection.

## Install

From your `cad-toolbox` virtual environment:

```bash
python3 -m pip install numpy scipy trimesh rtree manifold3d
```

## Run with defaults

```bash
python3 recipes/voronoi-lattice/trimesh/voronoi_lattice.py \
  path/to/model.stl
```

Default output:

```text
exports/
└── voronoi-lattice/
    └── model/
        ├── model-voronoi-lattice.stl
        ├── model-voronoi-lattice.glb
        └── model-voronoi-lattice.json
```

The filenames are intentionally stable. Re-running with changed parameters
overwrites these outputs, so FileBrowser Quantum shows the latest result
instead of accumulating duplicate versions.

## See every option

```bash
python3 recipes/voronoi-lattice/trimesh/voronoi_lattice.py --help
```

## Useful variations

Larger, more open cells:

```bash
python3 recipes/voronoi-lattice/trimesh/voronoi_lattice.py model.stl \
  --seeds 45 \
  --strut-radius 1.4
```

Denser organic structure:

```bash
python3 recipes/voronoi-lattice/trimesh/voronoi_lattice.py model.stl \
  --seeds 160 \
  --strut-radius 0.9 \
  --random-seed 91
```

Fast browser-preview pass before doing expensive booleans:

```bash
python3 recipes/voronoi-lattice/trimesh/voronoi_lattice.py model.stl \
  --preview-only
```

Try basic mesh repair:

```bash
python3 recipes/voronoi-lattice/trimesh/voronoi_lattice.py model.stl \
  --repair
```

High-quality final tessellation:

```bash
python3 recipes/voronoi-lattice/trimesh/voronoi_lattice.py model.stl \
  --quality high
```

## Parameter behavior

- `--seeds`: fewer produces large cells; more produces smaller, denser cells.
- `--strut-radius`: controls structural thickness.
- `--node-scale`: makes joints slightly thicker than struts.
- `--random-seed`: changes the cellular pattern while remaining deterministic.
- `--guard-margin` / `--guard-grid`: control helper sites that close otherwise
  infinite 3D Voronoi cells around the model.
- `--max-struts`: safety limit to avoid accidentally creating enormous boolean jobs.
- `--preview-only`: avoids union/intersection and is intended for fast visual tuning.

The script clamps dangerous values into model-relative safe ranges and prints
a `[guardrail]` message whenever it changes a requested value.

## Recommended iteration loop

```bash
python3 recipes/voronoi-lattice/trimesh/voronoi_lattice.py model.stl --preview-only
# inspect model-voronoi-lattice.glb in FileBrowser Quantum

python3 recipes/voronoi-lattice/trimesh/voronoi_lattice.py model.stl \
  --seeds 75 --strut-radius 1.2 --random-seed 7
# inspect the updated GLB
```

Use `--preview-only` while searching for a pattern you like, then remove it for
the boolean-clipped printable result.
