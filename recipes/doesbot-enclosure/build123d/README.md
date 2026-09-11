DOESBOT CNC Controller Enclosure — build123d

This is a from-scratch build123d rewrite of the original OpenSCAD enclosure.

Why this version is stronger

The model uses a centered mechanical coordinate system, explicit dataclass
configuration, typed connector definitions, BREP solids, independent STEP
exports, printable part layout, assembly/exploded exports, and parameter
validation.

The geometry is generated from stable constructive primitives rather than
depending heavily on topology-sensitive face/edge selection.

Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip build123d
```

Run

```bash
python doesbot_enclosure_build123d.py
```

Generated files:

```text
exports/
├── doesbot-bottom.step
├── doesbot-bottom.stl
├── doesbot-top.step
├── doesbot-top.stl
├── doesbot-pcb-reference.step
├── doesbot-assembly.step
├── doesbot-exploded.step
└── doesbot-print-layout.step
```

First measurements to replace

The original design still contains estimated/placeholder values for:

- PCB mounting-hole edge offsets
- component keep-out height
- connector centers and dimensions
- connector heights relative to PCB
- screw strategy / desired inserts or self-tapping hardware

Those are all isolated in the configuration and default_config() port map.

Repo placement

Recommended:

```text
cad-toolbox/
└── recipes/
    └── doesbot-cnc-enclosure/
        ├── README.md
        └── doesbot_enclosure_build123d.py
```