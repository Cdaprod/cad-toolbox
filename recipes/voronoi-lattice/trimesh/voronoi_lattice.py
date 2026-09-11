#!/usr/bin/env python3
"""
CAD Toolbox -- Voronoi Lattice / Surface Voronoi Modifier

Generate either:

    1. A true volumetric 3D Voronoi strut lattice inside a watertight solid.
    2. A surface-following Voronoi network over an arbitrary mesh.

The script can operate on an input model or generate built-in demo geometry.

ZERO-ARGUMENT DEMO
------------------

    python3 voronoi_lattice.py

Equivalent to:

    python3 voronoi_lattice.py --demo sphere

DEMO GEOMETRY
-------------

    python3 voronoi_lattice.py --demo sphere
    python3 voronoi_lattice.py --demo cube
    python3 voronoi_lattice.py --demo cylinder
    python3 voronoi_lattice.py --demo panel

Generate all demonstration geometries:

    python3 voronoi_lattice.py --demo all

MODES
-----

Volumetric lattice:

    python3 voronoi_lattice.py model.stl --mode volume

Surface-following Voronoi:

    python3 voronoi_lattice.py model.stl --mode surface

Only affect a selected box:

    python3 voronoi_lattice.py model.stl \
        --mode surface \
        --select-box -30 -30 -10 30 30 10

Only affect a spherical region:

    python3 voronoi_lattice.py model.stl \
        --mode surface \
        --select-sphere 0 0 20 35

Selections may be repeated and are unioned:

    --select-sphere 0 0 20 20 \
    --select-sphere 25 0 20 15

Invert them:

    --invert-selection

Preview selected source faces:

    --selection-preview

BRUSH SELECTION
---------------

A brush-selection JSON file may contain:

{
  "strokes": [
    {
      "radius": 15.0,
      "points": [
        [0, 0, 30],
        [10, 0, 28],
        [20, 5, 25]
      ]
    }
  ]
}

Then:

    python3 voronoi_lattice.py model.stl \
        --mode surface \
        --selection-file my-selection.json

The brush-selection backend is intentionally independent from the eventual GUI.
A Blender/FreeCAD/browser brush frontend only needs to emit the JSON format above.

DEPENDENCIES
------------

    python3 -m pip install numpy scipy trimesh rtree manifold3d

Recommended:

    python3 -m pip install pyglet

NOTES
-----

- Volume mode requires a closed/watertight source for reliable volume sampling.
- Surface mode works with non-watertight meshes.
- Printable volume mode uses manifold3d to union and clip the generated geometry.
- Surface mode generates struts centered on source-mesh Voronoi boundaries.
- Surface quality therefore improves with source mesh resolution.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import trimesh

from scipy.spatial import Voronoi, cKDTree


SUPPORTED_EXTENSIONS = {
    ".stl",
    ".obj",
    ".ply",
    ".glb",
    ".gltf",
    ".3mf",
}


DEMO_NAMES = (
    "sphere",
    "cube",
    "cylinder",
    "panel",
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class EffectiveConfig:
    input: str
    source_kind: str
    demo: str | None

    mode: str

    output_dir: str
    output_name: str

    seeds: int

    strut_radius_mm: float
    node_radius_mm: float

    guard_margin_mm: float
    guard_grid: int

    quality: str
    cylinder_sections: int

    max_struts: int

    random_seed: int

    preview_only: bool
    selection_preview: bool
    repair: bool

    selection_enabled: bool
    invert_selection: bool
    selection_dilate: int
    selection_erode: int

    source_extents_mm: list[float]
    source_diagonal_mm: float


@dataclass
class BrushStroke:
    radius: float
    points: np.ndarray


# ---------------------------------------------------------------------------
# Logging / guardrails
# ---------------------------------------------------------------------------


def info(message: str) -> None:
    print(f"[voronoi] {message}")


def warn(message: str) -> None:
    print(f"[guardrail] {message}", file=sys.stderr)


def clamp(
    value: float,
    low: float,
    high: float,
    label: str,
) -> float:
    if value < low:
        warn(
            f"{label} {value:g} is too small; "
            f"using {low:g}."
        )
        return low

    if value > high:
        warn(
            f"{label} {value:g} is too large; "
            f"using {high:g}."
        )
        return high

    return value


def clamp_int(
    value: int,
    low: int,
    high: int,
    label: str,
) -> int:
    if value < low:
        warn(
            f"{label} {value} is too small; "
            f"using {low}."
        )
        return low

    if value > high:
        warn(
            f"{label} {value} is too large; "
            f"using {high}."
        )
        return high

    return value


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def require_runtime_dependencies(
    *,
    mode: str,
    preview_only: bool,
) -> None:
    missing: list[str] = []

    if (
        mode == "volume"
        and importlib.util.find_spec("rtree") is None
    ):
        missing.append("rtree")

    if (
        mode == "volume"
        and not preview_only
        and importlib.util.find_spec("manifold3d") is None
    ):
        missing.append("manifold3d")

    if missing:
        packages = " ".join(missing)

        raise RuntimeError(
            "Missing runtime dependency/dependencies: "
            + ", ".join(missing)
            + "\n\nInstall with:\n"
            + f"  python3 -m pip install {packages}"
        )


# ---------------------------------------------------------------------------
# Built-in demonstration geometry
# ---------------------------------------------------------------------------


def make_demo_mesh(
    name: str,
) -> trimesh.Trimesh:
    """
    Generate predictable mm-scale demonstration solids.

    Sphere:
        Best organic surface demo.

    Cube:
        Shows Voronoi behavior across hard corners.

    Cylinder:
        Useful approximation for handles/grips/tubes.

    Panel:
        Useful for enclosure walls and approximately planar projections.
    """

    if name == "sphere":
        mesh = trimesh.creation.icosphere(
            subdivisions=4,
            radius=30.0,
        )

    elif name == "cube":
        mesh = trimesh.creation.box(
            extents=[60.0, 60.0, 60.0],
        )

        # Give surface mode enough triangles to establish useful
        # Voronoi boundaries rather than six giant planar polygons.
        mesh = subdivide_for_surface(
            mesh,
            max_edge=5.0,
            max_faces=50000,
        )

    elif name == "cylinder":
        mesh = trimesh.creation.cylinder(
            radius=30.0,
            height=60.0,
            sections=96,
        )

        mesh = subdivide_for_surface(
            mesh,
            max_edge=5.0,
            max_faces=50000,
        )

    elif name == "panel":
        mesh = trimesh.creation.box(
            extents=[80.0, 60.0, 4.0],
        )

        mesh = subdivide_for_surface(
            mesh,
            max_edge=4.0,
            max_faces=50000,
        )

    else:
        raise ValueError(
            f"Unknown demo geometry: {name}"
        )

    mesh.remove_unreferenced_vertices()

    return mesh


# ---------------------------------------------------------------------------
# Mesh loading / repair
# ---------------------------------------------------------------------------


def load_mesh(
    path: Path,
) -> trimesh.Trimesh:
    loaded = trimesh.load(
        path,
        force="scene",
    )

    if isinstance(
        loaded,
        trimesh.Trimesh,
    ):
        mesh = loaded.copy()

    elif isinstance(
        loaded,
        trimesh.Scene,
    ):
        meshes: list[trimesh.Trimesh] = []

        for geometry in loaded.geometry.values():
            if isinstance(
                geometry,
                trimesh.Trimesh,
            ):
                meshes.append(
                    geometry.copy()
                )

        if not meshes:
            raise ValueError(
                f"No mesh geometry found in {path}"
            )

        mesh = trimesh.util.concatenate(
            meshes
        )

    else:
        raise TypeError(
            "Unsupported geometry type: "
            f"{type(loaded).__name__}"
        )

    mesh.remove_unreferenced_vertices()

    return mesh


def try_repair(
    mesh: trimesh.Trimesh,
) -> trimesh.Trimesh:
    repaired = mesh.copy()

    try:
        trimesh.repair.fix_normals(
            repaired,
            multibody=True,
        )
    except Exception:
        pass

    try:
        trimesh.repair.fill_holes(
            repaired
        )
    except Exception:
        pass

    repaired.remove_unreferenced_vertices()

    return repaired


# ---------------------------------------------------------------------------
# Surface subdivision
# ---------------------------------------------------------------------------


def subdivide_for_surface(
    mesh: trimesh.Trimesh,
    *,
    max_edge: float,
    max_faces: int,
) -> trimesh.Trimesh:
    """
    Increase mesh resolution enough for surface Voronoi extraction.

    Surface mode derives boundaries from adjacent source triangles.
    Therefore extremely coarse meshes require subdivision.

    This function is bounded by max_faces to prevent accidental explosions.
    """

    result = mesh.copy()

    for _ in range(6):
        if len(result.faces) >= max_faces:
            break

        edges = result.edges_unique

        if len(edges) == 0:
            break

        lengths = np.linalg.norm(
            result.vertices[edges[:, 0]]
            - result.vertices[edges[:, 1]],
            axis=1,
        )

        if float(np.max(lengths)) <= max_edge:
            break

        new_vertices, new_faces = trimesh.remesh.subdivide(
            result.vertices,
            result.faces,
        )

        if len(new_faces) > max_faces:
            break

        result = trimesh.Trimesh(
            vertices=new_vertices,
            faces=new_faces,
            process=False,
        )

    result.remove_unreferenced_vertices()

    return result


# ---------------------------------------------------------------------------
# Selection parser / brush strokes
# ---------------------------------------------------------------------------


def load_brush_selection(
    path: Path,
) -> list[BrushStroke]:
    data = json.loads(
        path.read_text()
    )

    strokes_raw = data.get(
        "strokes",
        [],
    )

    strokes: list[BrushStroke] = []

    for index, raw in enumerate(strokes_raw):
        radius = float(
            raw.get(
                "radius",
                10.0,
            )
        )

        if radius <= 0:
            warn(
                f"Brush stroke {index} has invalid radius "
                f"{radius}; skipping."
            )
            continue

        points = np.asarray(
            raw.get(
                "points",
                [],
            ),
            dtype=float,
        )

        if (
            points.ndim != 2
            or points.shape[1] != 3
            or len(points) == 0
        ):
            warn(
                f"Brush stroke {index} contains no valid XYZ points; "
                "skipping."
            )
            continue

        strokes.append(
            BrushStroke(
                radius=radius,
                points=points,
            )
        )

    return strokes


def has_selection(
    args: argparse.Namespace,
) -> bool:
    return bool(
        args.select_box
        or args.select_sphere
        or args.selection_file
    )


def points_inside_selection(
    points: np.ndarray,
    *,
    boxes: Sequence[Sequence[float]],
    spheres: Sequence[Sequence[float]],
    brushes: Sequence[BrushStroke],
    invert: bool,
    margin: float,
) -> np.ndarray:
    """
    Return boolean mask for arbitrary XYZ points.

    Multiple regions are UNIONED.

    If no regions exist, everything is selected.
    """

    count = len(points)

    if (
        not boxes
        and not spheres
        and not brushes
    ):
        mask = np.ones(
            count,
            dtype=bool,
        )

        return ~mask if invert else mask

    mask = np.zeros(
        count,
        dtype=bool,
    )

    # -------------------------------------------------------
    # Boxes
    # -------------------------------------------------------

    for values in boxes:
        values = np.asarray(
            values,
            dtype=float,
        )

        low = np.minimum(
            values[:3],
            values[3:],
        ) - margin

        high = np.maximum(
            values[:3],
            values[3:],
        ) + margin

        inside = np.all(
            (points >= low)
            & (points <= high),
            axis=1,
        )

        mask |= inside

    # -------------------------------------------------------
    # Spheres
    # -------------------------------------------------------

    for values in spheres:
        values = np.asarray(
            values,
            dtype=float,
        )

        center = values[:3]
        radius = max(
            float(values[3]) + margin,
            0.0,
        )

        distance_squared = np.sum(
            (points - center) ** 2,
            axis=1,
        )

        mask |= (
            distance_squared
            <= radius * radius
        )

    # -------------------------------------------------------
    # Brush strokes
    # -------------------------------------------------------

    for stroke in brushes:
        radius = max(
            stroke.radius + margin,
            0.0,
        )

        tree = cKDTree(
            stroke.points
        )

        distances, _ = tree.query(
            points,
            k=1,
        )

        mask |= distances <= radius

    if invert:
        mask = ~mask

    return mask


# ---------------------------------------------------------------------------
# Face-mask morphology
# ---------------------------------------------------------------------------


def build_face_neighbors(
    mesh: trimesh.Trimesh,
) -> list[set[int]]:
    neighbors: list[set[int]] = [
        set()
        for _ in range(len(mesh.faces))
    ]

    for a, b in mesh.face_adjacency:
        a = int(a)
        b = int(b)

        neighbors[a].add(b)
        neighbors[b].add(a)

    return neighbors


def dilate_face_mask(
    mask: np.ndarray,
    neighbors: list[set[int]],
    iterations: int,
) -> np.ndarray:
    current = mask.copy()

    for _ in range(iterations):
        expanded = current.copy()

        selected = np.flatnonzero(
            current
        )

        for face_index in selected:
            for neighbor in neighbors[
                int(face_index)
            ]:
                expanded[neighbor] = True

        current = expanded

    return current


def erode_face_mask(
    mask: np.ndarray,
    neighbors: list[set[int]],
    iterations: int,
) -> np.ndarray:
    current = mask.copy()

    for _ in range(iterations):
        eroded = current.copy()

        selected = np.flatnonzero(
            current
        )

        for face_index in selected:
            face_index = int(
                face_index
            )

            if any(
                not current[n]
                for n in neighbors[face_index]
            ):
                eroded[face_index] = False

        current = eroded

    return current


def cleanup_face_selection(
    mesh: trimesh.Trimesh,
    mask: np.ndarray,
    *,
    dilate_iterations: int,
    erode_iterations: int,
) -> np.ndarray:
    if (
        dilate_iterations == 0
        and erode_iterations == 0
    ):
        return mask

    neighbors = build_face_neighbors(
        mesh
    )

    result = mask

    if dilate_iterations > 0:
        result = dilate_face_mask(
            result,
            neighbors,
            dilate_iterations,
        )

    if erode_iterations > 0:
        result = erode_face_mask(
            result,
            neighbors,
            erode_iterations,
        )

    return result


# ---------------------------------------------------------------------------
# Selection preview
# ---------------------------------------------------------------------------


def export_selection_preview(
    source: trimesh.Trimesh,
    selected_faces: np.ndarray,
    output_dir: Path,
    output_name: str,
) -> Path:
    """
    Export a GLB with selected faces highlighted.

    Blue-ish neutral:
        unaffected faces

    Red:
        selected modifier area
    """

    preview = source.copy()

    colors = np.tile(
        np.array(
            [110, 120, 135, 100],
            dtype=np.uint8,
        ),
        (len(preview.faces), 1),
    )

    colors[selected_faces] = np.array(
        [235, 70, 70, 255],
        dtype=np.uint8,
    )

    preview.visual.face_colors = colors

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        output_dir
        / f"{output_name}-selection-preview.glb"
    )

    preview.export(
        path
    )

    return path


# ---------------------------------------------------------------------------
# Volume-mode sampling
# ---------------------------------------------------------------------------


def volume_sample(
    mesh: trimesh.Trimesh,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    collected: list[np.ndarray] = []

    total = 0

    np.random.seed(
        int(
            rng.integers(
                0,
                2**31 - 1,
            )
        )
    )

    for _ in range(12):
        need = count - total

        if need <= 0:
            break

        batch_request = max(
            need * 3,
            64,
        )

        pts = trimesh.sample.volume_mesh(
            mesh,
            batch_request,
        )

        if len(pts):
            pts = np.asarray(
                pts,
                dtype=float,
            )

            if len(pts) > need:
                choose = rng.choice(
                    len(pts),
                    size=need,
                    replace=False,
                )

                pts = pts[choose]

            collected.append(
                pts
            )

            total += len(pts)

    if not collected:
        raise RuntimeError(
            "Could not sample points inside the model. "
            "The source mesh likely is not a closed volume."
        )

    points = np.vstack(
        collected
    )

    if len(points) < count:
        warn(
            f"Requested {count} interior seeds but only "
            f"found {len(points)}."
        )

    return points[:count]


# ---------------------------------------------------------------------------
# Volume Voronoi
# ---------------------------------------------------------------------------


def guard_points(
    bounds: np.ndarray,
    margin: float,
    grid: int,
) -> np.ndarray:
    bmin = bounds[0] - margin
    bmax = bounds[1] + margin

    axes = [
        np.linspace(
            bmin[i],
            bmax[i],
            grid,
        )
        for i in range(3)
    ]

    pts: list[
        tuple[
            float,
            float,
            float,
        ]
    ] = []

    for y in axes[1]:
        for z in axes[2]:
            pts.append(
                (
                    bmin[0],
                    y,
                    z,
                )
            )

            pts.append(
                (
                    bmax[0],
                    y,
                    z,
                )
            )

    for x in axes[0]:
        for z in axes[2]:
            pts.append(
                (
                    x,
                    bmin[1],
                    z,
                )
            )

            pts.append(
                (
                    x,
                    bmax[1],
                    z,
                )
            )

    for x in axes[0]:
        for y in axes[1]:
            pts.append(
                (
                    x,
                    y,
                    bmin[2],
                )
            )

            pts.append(
                (
                    x,
                    y,
                    bmax[2],
                )
            )

    array = np.asarray(
        pts,
        dtype=float,
    )

    return np.unique(
        np.round(
            array,
            decimals=9,
        ),
        axis=0,
    )


def edge_key(
    a: np.ndarray,
    b: np.ndarray,
    quant: float,
) -> tuple:
    qa = tuple(
        np.round(
            a / quant
        ).astype(
            np.int64
        )
    )

    qb = tuple(
        np.round(
            b / quant
        ).astype(
            np.int64
        )
    )

    return (
        (qa, qb)
        if qa <= qb
        else (qb, qa)
    )


def voronoi_segments_volume(
    interior: np.ndarray,
    guards: np.ndarray,
    *,
    min_length: float,
    max_length: float,
    quantization: float,
) -> list[
    tuple[
        np.ndarray,
        np.ndarray,
    ]
]:
    points = np.vstack(
        [
            interior,
            guards,
        ]
    )

    vor = Voronoi(
        points
    )

    interior_count = len(
        interior
    )

    segments: dict[
        tuple,
        tuple[
            np.ndarray,
            np.ndarray,
        ],
    ] = {}

    for sites, ridge_vertex_ids in zip(
        vor.ridge_points,
        vor.ridge_vertices,
    ):
        if (
            sites[0] >= interior_count
            and sites[1] >= interior_count
        ):
            continue

        if (
            len(ridge_vertex_ids) < 2
            or -1 in ridge_vertex_ids
        ):
            continue

        poly = vor.vertices[
            np.asarray(
                ridge_vertex_ids,
                dtype=int,
            )
        ]

        if not np.isfinite(
            poly
        ).all():
            continue

        for i in range(
            len(poly)
        ):
            a = poly[i]

            b = poly[
                (i + 1)
                % len(poly)
            ]

            length = float(
                np.linalg.norm(
                    b - a
                )
            )

            if (
                length < min_length
                or length > max_length
            ):
                continue

            key = edge_key(
                a,
                b,
                quantization,
            )

            segments.setdefault(
                key,
                (
                    a,
                    b,
                ),
            )

    return list(
        segments.values()
    )


# ---------------------------------------------------------------------------
# Surface Voronoi
# ---------------------------------------------------------------------------


def surface_seed_points(
    mesh: trimesh.Trimesh,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Sample Voronoi sites directly from the source surface.
    """

    np.random.seed(
        int(
            rng.integers(
                0,
                2**31 - 1,
            )
        )
    )

    points, _ = trimesh.sample.sample_surface_even(
        mesh,
        count,
    )

    points = np.asarray(
        points,
        dtype=float,
    )

    if len(points) < count:
        missing = count - len(points)

        extra, _ = trimesh.sample.sample_surface(
            mesh,
            missing,
        )

        points = np.vstack(
            [
                points,
                extra,
            ]
        )

    return points[:count]


def voronoi_segments_surface(
    mesh: trimesh.Trimesh,
    seeds: np.ndarray,
    *,
    selected_faces: np.ndarray,
    min_length: float,
    max_length: float,
    selection_edge_mode: str,
) -> list[
    tuple[
        np.ndarray,
        np.ndarray,
    ]
]:
    """
    Create a discrete surface-following Voronoi network.

    Each source triangle is assigned to its nearest surface seed.

    Edges shared by triangles belonging to different seed regions form the
    Voronoi cell boundaries.

    This avoids planar XY projection and therefore works over curved
    arbitrary geometry.
    """

    face_centers = np.asarray(
        mesh.triangles_center,
        dtype=float,
    )

    tree = cKDTree(
        seeds
    )

    _, labels = tree.query(
        face_centers,
        k=1,
    )

    labels = np.asarray(
        labels,
        dtype=np.int64,
    )

    segments: list[
        tuple[
            np.ndarray,
            np.ndarray,
        ]
    ] = []

    for adjacency, edge in zip(
        mesh.face_adjacency,
        mesh.face_adjacency_edges,
    ):
        face_a = int(
            adjacency[0]
        )

        face_b = int(
            adjacency[1]
        )

        if labels[face_a] == labels[face_b]:
            continue

        if selection_edge_mode == "both":
            allowed = (
                selected_faces[face_a]
                and selected_faces[face_b]
            )

        elif selection_edge_mode == "either":
            allowed = (
                selected_faces[face_a]
                or selected_faces[face_b]
            )

        else:
            raise ValueError(
                "Unknown selection edge mode: "
                f"{selection_edge_mode}"
            )

        if not allowed:
            continue

        a = mesh.vertices[
            int(edge[0])
        ]

        b = mesh.vertices[
            int(edge[1])
        ]

        length = float(
            np.linalg.norm(
                b - a
            )
        )

        if (
            length < min_length
            or length > max_length
        ):
            continue

        segments.append(
            (
                np.asarray(
                    a,
                    dtype=float,
                ),
                np.asarray(
                    b,
                    dtype=float,
                ),
            )
        )

    return segments


# ---------------------------------------------------------------------------
# Segment selection
# ---------------------------------------------------------------------------


def filter_segments_selection(
    segments: list[
        tuple[
            np.ndarray,
            np.ndarray,
        ]
    ],
    *,
    boxes: Sequence[Sequence[float]],
    spheres: Sequence[Sequence[float]],
    brushes: Sequence[BrushStroke],
    invert: bool,
    margin: float,
    mode: str,
) -> list[
    tuple[
        np.ndarray,
        np.ndarray,
    ]
]:
    if (
        not boxes
        and not spheres
        and not brushes
    ):
        return segments

    kept: list[
        tuple[
            np.ndarray,
            np.ndarray,
        ]
    ] = []

    for a, b in segments:
        midpoint = (
            a + b
        ) * 0.5

        samples = np.vstack(
            [
                a,
                midpoint,
                b,
            ]
        )

        mask = points_inside_selection(
            samples,
            boxes=boxes,
            spheres=spheres,
            brushes=brushes,
            invert=invert,
            margin=margin,
        )

        if mode == "midpoint":
            include = bool(
                mask[1]
            )

        elif mode == "touch":
            include = bool(
                np.any(mask)
            )

        elif mode == "inside":
            include = bool(
                np.all(mask)
            )

        else:
            raise ValueError(
                f"Unknown segment selection mode: {mode}"
            )

        if include:
            kept.append(
                (
                    a,
                    b,
                )
            )

    return kept


# ---------------------------------------------------------------------------
# Segment reduction
# ---------------------------------------------------------------------------


def reduce_segments(
    segments: list[
        tuple[
            np.ndarray,
            np.ndarray,
        ]
    ],
    max_struts: int,
    rng: np.random.Generator,
) -> list[
    tuple[
        np.ndarray,
        np.ndarray,
    ]
]:
    if len(
        segments
    ) <= max_struts:
        return segments

    warn(
        f"Voronoi produced {len(segments)} struts; "
        f"limiting to {max_struts}."
    )

    ids = np.sort(
        rng.choice(
            len(segments),
            size=max_struts,
            replace=False,
        )
    )

    return [
        segments[i]
        for i in ids
    ]


# ---------------------------------------------------------------------------
# Lattice geometry
# ---------------------------------------------------------------------------


def build_lattice_pieces(
    segments: Iterable[
        tuple[
            np.ndarray,
            np.ndarray,
        ]
    ],
    *,
    strut_radius: float,
    node_radius: float,
    cylinder_sections: int,
    node_subdivisions: int,
    add_nodes: bool,
) -> list[
    trimesh.Trimesh
]:
    pieces: list[
        trimesh.Trimesh
    ] = []

    nodes: dict[
        tuple[
            int,
            int,
            int,
        ],
        np.ndarray,
    ] = {}

    quant = max(
        strut_radius * 0.2,
        1e-6,
    )

    for a, b in segments:
        if (
            np.linalg.norm(
                b - a
            )
            <= 1e-9
        ):
            continue

        cylinder = trimesh.creation.cylinder(
            radius=strut_radius,
            segment=np.vstack(
                [
                    a,
                    b,
                ]
            ),
            sections=cylinder_sections,
        )

        pieces.append(
            cylinder
        )

        if add_nodes:
            for point in (
                a,
                b,
            ):
                key = tuple(
                    np.round(
                        point / quant
                    ).astype(
                        np.int64
                    )
                )

                nodes.setdefault(
                    key,
                    point,
                )

    if add_nodes:
        for point in nodes.values():
            sphere = trimesh.creation.icosphere(
                subdivisions=node_subdivisions,
                radius=node_radius,
            )

            sphere.apply_translation(
                point
            )

            pieces.append(
                sphere
            )

    return pieces


# ---------------------------------------------------------------------------
# Booleans
# ---------------------------------------------------------------------------


def union_chunked(
    meshes: list[
        trimesh.Trimesh
    ],
    *,
    chunk_size: int = 120,
) -> trimesh.Trimesh:
    if not meshes:
        raise RuntimeError(
            "No lattice pieces were generated."
        )

    def union_group(
        group: list[
            trimesh.Trimesh
        ],
    ) -> trimesh.Trimesh:
        if len(
            group
        ) == 1:
            return group[0]

        result = trimesh.boolean.union(
            group,
            engine="manifold",
            check_volume=False,
        )

        if result is None:
            raise RuntimeError(
                "manifold boolean union returned no geometry."
            )

        if isinstance(
            result,
            list,
        ):
            result = trimesh.util.concatenate(
                result
            )

        return result

    current = meshes

    while len(
        current
    ) > 1:
        next_round: list[
            trimesh.Trimesh
        ] = []

        for start in range(
            0,
            len(current),
            chunk_size,
        ):
            next_round.append(
                union_group(
                    current[
                        start:
                        start + chunk_size
                    ]
                )
            )

        current = next_round

    return current[0]


def intersect_with_source(
    lattice: trimesh.Trimesh,
    source: trimesh.Trimesh,
) -> trimesh.Trimesh:
    result = trimesh.boolean.intersection(
        [
            lattice,
            source,
        ],
        engine="manifold",
        check_volume=False,
    )

    if result is None:
        raise RuntimeError(
            "manifold intersection returned no geometry."
        )

    if isinstance(
        result,
        list,
    ):
        result = trimesh.util.concatenate(
            result
        )

    return result


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_outputs(
    mesh: trimesh.Trimesh,
    output_dir: Path,
    output_name: str,
    config: EffectiveConfig,
) -> None:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    prefix = (
        f"{output_name}-voronoi-{config.mode}"
    )

    stl_path = (
        output_dir
        / f"{prefix}.stl"
    )

    glb_path = (
        output_dir
        / f"{prefix}.glb"
    )

    json_path = (
        output_dir
        / f"{prefix}.json"
    )

    mesh.export(
        stl_path
    )

    mesh.export(
        glb_path
    )

    manifest = asdict(
        config
    )

    manifest[
        "generated_unix_time"
    ] = time.time()

    manifest[
        "vertices"
    ] = int(
        len(mesh.vertices)
    )

    manifest[
        "faces"
    ] = int(
        len(mesh.faces)
    )

    manifest[
        "watertight"
    ] = bool(
        mesh.is_watertight
    )

    json_path.write_text(
        json.dumps(
            manifest,
            indent=2,
        )
        + "\n"
    )

    print()

    info(
        "Generated Voronoi output:"
    )

    print(
        f"  STL:       {stl_path.resolve()}"
    )

    print(
        f"  GLB:       {glb_path.resolve()}"
    )

    print(
        f"  Manifest:  {json_path.resolve()}"
    )

    print(
        f"  Vertices:  {len(mesh.vertices):,}"
    )

    print(
        f"  Faces:     {len(mesh.faces):,}"
    )

    print(
        "  Watertight:"
        f"{' yes' if mesh.is_watertight else ' no'}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate either a true volumetric 3D Voronoi lattice "
            "or a surface-following Voronoi network."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help=(
            "Input mesh: STL, OBJ, PLY, GLB, GLTF, or 3MF. "
            "If omitted, the sphere demo is generated."
        ),
    )

    parser.add_argument(
        "--demo",
        choices=(
            *DEMO_NAMES,
            "all",
        ),
        default=None,
        help=(
            "Use built-in geometry instead of an input file."
        ),
    )

    parser.add_argument(
        "--mode",
        choices=(
            "volume",
            "surface",
        ),
        default="surface",
        help=(
            "volume = true interior 3D lattice; "
            "surface = Voronoi network following the source surface."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Destination directory. Default: "
            "exports/voronoi-lattice/<source>/"
        ),
    )

    parser.add_argument(
        "--output-name",
        default=None,
        help=(
            "Base filename."
        ),
    )

    # -------------------------------------------------------
    # Voronoi controls
    # -------------------------------------------------------

    parser.add_argument(
        "--seeds",
        type=int,
        default=85,
        help=(
            "Voronoi seed count. "
            "Guardrailed to 12..400."
        ),
    )

    parser.add_argument(
        "--strut-radius",
        type=float,
        default=None,
        metavar="MM",
        help=(
            "Voronoi strut radius. "
            "Default scales with model size."
        ),
    )

    parser.add_argument(
        "--node-scale",
        type=float,
        default=1.12,
        help=(
            "Node sphere radius / strut radius."
        ),
    )

    parser.add_argument(
        "--no-nodes",
        action="store_true",
        help=(
            "Do not add spherical joints at strut endpoints."
        ),
    )

    # -------------------------------------------------------
    # Volume mode
    # -------------------------------------------------------

    parser.add_argument(
        "--guard-margin",
        type=float,
        default=None,
        metavar="MM",
        help=(
            "Volume-mode helper Voronoi boundary distance."
        ),
    )

    parser.add_argument(
        "--guard-grid",
        type=int,
        default=3,
        help=(
            "Points per helper bounding-box face axis."
        ),
    )

    # -------------------------------------------------------
    # Surface resolution
    # -------------------------------------------------------

    parser.add_argument(
        "--surface-max-edge",
        type=float,
        default=None,
        metavar="MM",
        help=(
            "Subdivide surface mode until mesh edges are approximately "
            "this size. Default scales with source size."
        ),
    )

    parser.add_argument(
        "--surface-max-faces",
        type=int,
        default=60000,
        help=(
            "Safety ceiling on surface subdivision."
        ),
    )

    # -------------------------------------------------------
    # Selection geometry
    # -------------------------------------------------------

    parser.add_argument(
        "--select-box",
        nargs=6,
        type=float,
        action="append",
        metavar=(
            "XMIN",
            "YMIN",
            "ZMIN",
            "XMAX",
            "YMAX",
            "ZMAX",
        ),
        default=[],
        help=(
            "Restrict modifier to an XYZ box. "
            "Repeatable."
        ),
    )

    parser.add_argument(
        "--select-sphere",
        nargs=4,
        type=float,
        action="append",
        metavar=(
            "X",
            "Y",
            "Z",
            "R",
        ),
        default=[],
        help=(
            "Restrict modifier to a spherical region. "
            "Repeatable."
        ),
    )

    parser.add_argument(
        "--selection-file",
        type=Path,
        default=None,
        help=(
            "Brush-selection JSON file."
        ),
    )

    parser.add_argument(
        "--selection-margin",
        type=float,
        default=0.0,
        metavar="MM",
        help=(
            "Expand selection regions by this distance."
        ),
    )

    parser.add_argument(
        "--invert-selection",
        action="store_true",
        help=(
            "Apply modifier outside the selected region instead."
        ),
    )

    parser.add_argument(
        "--segment-selection",
        choices=(
            "midpoint",
            "touch",
            "inside",
        ),
        default="midpoint",
        help=(
            "How volume struts are accepted against a selection."
        ),
    )

    parser.add_argument(
        "--surface-selection-edge",
        choices=(
            "both",
            "either",
        ),
        default="both",
        help=(
            "Require both adjacent surface faces to be selected, "
            "or permit either one."
        ),
    )

    # -------------------------------------------------------
    # Selection cleanup
    # -------------------------------------------------------

    parser.add_argument(
        "--selection-dilate",
        type=int,
        default=1,
        help=(
            "Surface-face expansion iterations. "
            "Useful for eliminating tiny missed gaps."
        ),
    )

    parser.add_argument(
        "--selection-erode",
        type=int,
        default=0,
        help=(
            "Surface-face shrink iterations."
        ),
    )

    parser.add_argument(
        "--selection-preview",
        action="store_true",
        help=(
            "Export selected source faces as a colored GLB and exit."
        ),
    )

    # -------------------------------------------------------
    # General quality / safety
    # -------------------------------------------------------

    parser.add_argument(
        "--max-struts",
        type=int,
        default=1800,
        help=(
            "Safety cap on generated struts."
        ),
    )

    parser.add_argument(
        "--quality",
        choices=(
            "low",
            "medium",
            "high",
        ),
        default="medium",
        help=(
            "Cylinder and node tessellation quality."
        ),
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help=(
            "Deterministic random seed."
        ),
    )

    parser.add_argument(
        "--preview-only",
        action="store_true",
        help=(
            "Skip volume-mode boolean union/clipping. "
            "Fast but may contain overlapping geometry."
        ),
    )

    parser.add_argument(
        "--repair",
        action="store_true",
        help=(
            "Attempt basic mesh repair before processing."
        ),
    )

    return parser


# ---------------------------------------------------------------------------
# Single model execution
# ---------------------------------------------------------------------------


def process_source(
    *,
    args: argparse.Namespace,
    source: trimesh.Trimesh,
    source_name: str,
    input_label: str,
    demo_name: str | None,
) -> int:
    if args.repair:
        source = try_repair(
            source
        )

    source.remove_unreferenced_vertices()

    extents = np.asarray(
        source.extents,
        dtype=float,
    )

    if (
        np.any(
            ~np.isfinite(
                extents
            )
        )
        or np.any(
            extents <= 0
        )
    ):
        raise RuntimeError(
            f"Invalid source extents: {extents}"
        )

    diagonal = float(
        np.linalg.norm(
            extents
        )
    )

    min_extent = float(
        np.min(
            extents
        )
    )

    # -------------------------------------------------------
    # Guardrailed parameters
    # -------------------------------------------------------

    seeds = clamp_int(
        args.seeds,
        12,
        400,
        "seeds",
    )

    guard_grid = clamp_int(
        args.guard_grid,
        2,
        5,
        "guard-grid",
    )

    max_struts = clamp_int(
        args.max_struts,
        100,
        5000,
        "max-struts",
    )

    node_scale = clamp(
        args.node_scale,
        1.0,
        1.8,
        "node-scale",
    )

    surface_max_faces = clamp_int(
        args.surface_max_faces,
        1000,
        250000,
        "surface-max-faces",
    )

    selection_dilate = clamp_int(
        args.selection_dilate,
        0,
        20,
        "selection-dilate",
    )

    selection_erode = clamp_int(
        args.selection_erode,
        0,
        20,
        "selection-erode",
    )

    # -------------------------------------------------------
    # Radius scaling
    # -------------------------------------------------------

    min_radius = max(
        min_extent * 0.0015,
        0.05,
    )

    max_radius = max(
        min_extent * 0.08,
        min_radius,
    )

    default_radius = (
        min_extent * 0.0115
    )

    strut_radius = clamp(
        (
            default_radius
            if args.strut_radius is None
            else args.strut_radius
        ),
        min_radius,
        max_radius,
        "strut-radius",
    )

    node_radius = (
        strut_radius
        * node_scale
    )

    # -------------------------------------------------------
    # Guard box
    # -------------------------------------------------------

    min_guard = (
        diagonal * 0.04
    )

    max_guard = (
        diagonal * 0.75
    )

    default_guard = (
        diagonal * 0.18
    )

    guard_margin = clamp(
        (
            default_guard
            if args.guard_margin is None
            else args.guard_margin
        ),
        min_guard,
        max_guard,
        "guard-margin",
    )

    # -------------------------------------------------------
    # Surface tessellation size
    # -------------------------------------------------------

    default_surface_edge = max(
        diagonal / 50.0,
        strut_radius * 1.25,
    )

    surface_max_edge = clamp(
        (
            default_surface_edge
            if args.surface_max_edge is None
            else args.surface_max_edge
        ),
        max(
            diagonal / 500.0,
            0.1,
        ),
        max(
            diagonal / 5.0,
            0.5,
        ),
        "surface-max-edge",
    )

    # -------------------------------------------------------
    # Quality
    # -------------------------------------------------------

    quality_map = {
        "low": (
            6,
            1,
        ),
        "medium": (
            10,
            1,
        ),
        "high": (
            16,
            2,
        ),
    }

    (
        cylinder_sections,
        node_subdivisions,
    ) = quality_map[
        args.quality
    ]

    # -------------------------------------------------------
    # Output
    # -------------------------------------------------------

    output_name = (
        args.output_name
        or source_name
    )

    output_dir = (
        args.output_dir.expanduser()
        if args.output_dir is not None
        else (
            Path("exports")
            / "voronoi-lattice"
            / source_name
        )
    )

    # -------------------------------------------------------
    # Selection
    # -------------------------------------------------------

    brushes: list[
        BrushStroke
    ] = []

    if args.selection_file:
        selection_file = (
            args.selection_file
            .expanduser()
            .resolve()
        )

        if not selection_file.exists():
            raise FileNotFoundError(
                f"Selection file not found: "
                f"{selection_file}"
            )

        brushes = load_brush_selection(
            selection_file
        )

    selection_enabled = bool(
        args.select_box
        or args.select_sphere
        or brushes
    )

    # -------------------------------------------------------
    # Runtime dependencies
    # -------------------------------------------------------

    require_runtime_dependencies(
        mode=args.mode,
        preview_only=bool(
            args.preview_only
        ),
    )

    # -------------------------------------------------------
    # Watertight guardrail
    # -------------------------------------------------------

    if (
        args.mode == "volume"
        and not source.is_watertight
    ):
        message = (
            "Source mesh is not watertight. "
            "Volume sampling needs a closed solid."
        )

        if args.preview_only:
            warn(
                message
                + " Preview will still be attempted."
            )

        else:
            raise RuntimeError(
                message
                + "\nTry --repair or switch to --mode surface."
            )

    # -------------------------------------------------------
    # Status
    # -------------------------------------------------------

    print()

    info(
        "Voronoi modifier configuration"
    )

    print(
        f"  Source:           {input_label}"
    )

    print(
        f"  Mode:             {args.mode}"
    )

    print(
        "  Extents:          "
        f"{extents[0]:.3f} x "
        f"{extents[1]:.3f} x "
        f"{extents[2]:.3f} mm"
    )

    print(
        f"  Seeds:            {seeds}"
    )

    print(
        f"  Strut radius:     {strut_radius:.3f} mm"
    )

    print(
        f"  Node radius:      {node_radius:.3f} mm"
    )

    print(
        f"  Selection:        "
        f"{'enabled' if selection_enabled else 'entire model'}"
    )

    print(
        f"  Random seed:      {args.random_seed}"
    )

    rng = np.random.default_rng(
        args.random_seed
    )

    # =======================================================
    # SURFACE MODE
    # =======================================================

    if args.mode == "surface":
        source_work = subdivide_for_surface(
            source,
            max_edge=surface_max_edge,
            max_faces=surface_max_faces,
        )

        print(
            f"  Surface faces:    "
            f"{len(source_work.faces):,}"
        )

        face_centers = np.asarray(
            source_work.triangles_center,
            dtype=float,
        )

        selected_faces = points_inside_selection(
            face_centers,
            boxes=args.select_box,
            spheres=args.select_sphere,
            brushes=brushes,
            invert=bool(
                args.invert_selection
            ),
            margin=float(
                args.selection_margin
            ),
        )

        if selection_enabled:
            selected_faces = cleanup_face_selection(
                source_work,
                selected_faces,
                dilate_iterations=selection_dilate,
                erode_iterations=selection_erode,
            )

        print(
            f"  Selected faces:   "
            f"{np.count_nonzero(selected_faces):,}"
            f" / {len(selected_faces):,}"
        )

        if not np.any(
            selected_faces
        ):
            raise RuntimeError(
                "Selection contains no faces."
            )

        if args.selection_preview:
            preview_path = export_selection_preview(
                source_work,
                selected_faces,
                output_dir,
                output_name,
            )

            print()

            info(
                "Selection preview generated:"
            )

            print(
                f"  {preview_path.resolve()}"
            )

            return 0

        surface_seeds = surface_seed_points(
            source_work,
            seeds,
            rng,
        )

        min_segment = max(
            strut_radius * 0.75,
            diagonal * 0.0005,
        )

        max_segment = (
            diagonal * 0.20
        )

        segments = voronoi_segments_surface(
            source_work,
            surface_seeds,
            selected_faces=selected_faces,
            min_length=min_segment,
            max_length=max_segment,
            selection_edge_mode=args.surface_selection_edge,
        )

    # =======================================================
    # VOLUME MODE
    # =======================================================

    else:
        interior = volume_sample(
            source,
            seeds,
            rng,
        )

        guards = guard_points(
            source.bounds,
            guard_margin,
            guard_grid,
        )

        min_segment = max(
            strut_radius * 1.5,
            diagonal * 0.001,
        )

        max_segment = (
            diagonal * 0.80
        )

        quantization = max(
            strut_radius * 0.12,
            diagonal * 1e-6,
        )

        segments = voronoi_segments_volume(
            interior,
            guards,
            min_length=min_segment,
            max_length=max_segment,
            quantization=quantization,
        )

        segments = filter_segments_selection(
            segments,
            boxes=args.select_box,
            spheres=args.select_sphere,
            brushes=brushes,
            invert=bool(
                args.invert_selection
            ),
            margin=float(
                args.selection_margin
            ),
            mode=args.segment_selection,
        )

    # -------------------------------------------------------
    # Segment guardrails
    # -------------------------------------------------------

    if not segments:
        raise RuntimeError(
            "No Voronoi struts survived generation/selection.\n"
            "Try more seeds, a larger selection region, or a "
            "smaller strut radius."
        )

    segments = reduce_segments(
        segments,
        max_struts,
        rng,
    )

    print(
        f"  Voronoi struts:   "
        f"{len(segments):,}"
    )

    # -------------------------------------------------------
    # Build actual geometry
    # -------------------------------------------------------

    pieces = build_lattice_pieces(
        segments,
        strut_radius=strut_radius,
        node_radius=node_radius,
        cylinder_sections=cylinder_sections,
        node_subdivisions=node_subdivisions,
        add_nodes=not args.no_nodes,
    )

    print(
        f"  Mesh pieces:      "
        f"{len(pieces):,}"
    )

    # -------------------------------------------------------
    # Surface mode
    #
    # Struts lie directly on the surface and intentionally
    # straddle it. Do not clip them back into the solid,
    # because that would remove the external half.
    # -------------------------------------------------------

    if args.mode == "surface":
        if args.preview_only:
            result = trimesh.util.concatenate(
                pieces
            )

        else:
            # For surface mode union is desirable but not mandatory.
            # It requires manifold3d only if actually installed.
            if importlib.util.find_spec(
                "manifold3d"
            ):
                try:
                    result = union_chunked(
                        pieces
                    )
                except Exception as exc:
                    warn(
                        "Surface union failed; exporting "
                        "concatenated pieces instead. "
                        f"{exc}"
                    )

                    result = trimesh.util.concatenate(
                        pieces
                    )

            else:
                warn(
                    "manifold3d not installed; "
                    "surface result will contain overlapping "
                    "but geometrically valid strut pieces."
                )

                result = trimesh.util.concatenate(
                    pieces
                )

    # -------------------------------------------------------
    # Volume mode
    # -------------------------------------------------------

    elif args.preview_only:
        result = trimesh.util.concatenate(
            pieces
        )

    else:
        try:
            lattice = union_chunked(
                pieces
            )

            result = intersect_with_source(
                lattice,
                source,
            )

        except BaseException as exc:
            if (
                exc.__class__.__name__
                == "ModuleNotFoundError"
                or "manifold" in str(
                    exc
                ).lower()
            ):
                raise RuntimeError(
                    "Printable volume mode requires manifold3d.\n"
                    "\nInstall with:\n"
                    "  python3 -m pip install manifold3d\n"
                    "\nOr rerun using:\n"
                    "  --preview-only"
                ) from exc

            raise

    result.remove_unreferenced_vertices()

    # -------------------------------------------------------
    # Manifest
    # -------------------------------------------------------

    config = EffectiveConfig(
        input=input_label,
        source_kind=(
            "demo"
            if demo_name
            else "file"
        ),
        demo=demo_name,
        mode=args.mode,
        output_dir=str(
            output_dir
        ),
        output_name=output_name,
        seeds=seeds,
        strut_radius_mm=float(
            strut_radius
        ),
        node_radius_mm=float(
            node_radius
        ),
        guard_margin_mm=float(
            guard_margin
        ),
        guard_grid=guard_grid,
        quality=args.quality,
        cylinder_sections=cylinder_sections,
        max_struts=max_struts,
        random_seed=args.random_seed,
        preview_only=bool(
            args.preview_only
        ),
        selection_preview=bool(
            args.selection_preview
        ),
        repair=bool(
            args.repair
        ),
        selection_enabled=selection_enabled,
        invert_selection=bool(
            args.invert_selection
        ),
        selection_dilate=selection_dilate,
        selection_erode=selection_erode,
        source_extents_mm=[
            float(x)
            for x in extents
        ],
        source_diagonal_mm=diagonal,
    )

    export_outputs(
        result,
        output_dir,
        output_name,
        config,
    )

    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = make_parser()

    args = parser.parse_args()

    # -------------------------------------------------------
    # Input/demo resolution
    # -------------------------------------------------------

    if (
        args.input is not None
        and args.demo is not None
    ):
        parser.error(
            "Use either an input model OR --demo, not both."
        )

    # Zero arguments = sphere demonstration.
    if (
        args.input is None
        and args.demo is None
    ):
        args.demo = "sphere"

    # -------------------------------------------------------
    # Entire demo gallery
    # -------------------------------------------------------

    if args.demo == "all":
        original_output_name = (
            args.output_name
        )

        for demo_name in DEMO_NAMES:
            print()
            print(
                "=" * 72
            )

            info(
                f"DEMO: {demo_name}"
            )

            print(
                "=" * 72
            )

            source = make_demo_mesh(
                demo_name
            )

            args.output_name = (
                original_output_name
                or demo_name
            )

            process_source(
                args=args,
                source=source,
                source_name=demo_name,
                input_label=(
                    f"demo:{demo_name}"
                ),
                demo_name=demo_name,
            )

        return 0

    # -------------------------------------------------------
    # Single demo
    # -------------------------------------------------------

    if args.demo is not None:
        source = make_demo_mesh(
            args.demo
        )

        source_name = (
            args.demo
        )

        return process_source(
            args=args,
            source=source,
            source_name=source_name,
            input_label=(
                f"demo:{args.demo}"
            ),
            demo_name=args.demo,
        )

    # -------------------------------------------------------
    # Input model
    # -------------------------------------------------------

    assert args.input is not None

    input_path = (
        args.input
        .expanduser()
        .resolve()
    )

    if not input_path.exists():
        parser.error(
            f"Input does not exist: "
            f"{input_path}"
        )

    if (
        input_path.suffix.lower()
        not in SUPPORTED_EXTENSIONS
    ):
        parser.error(
            f"Unsupported extension "
            f"{input_path.suffix!r}.\n"
            "Supported: "
            + ", ".join(
                sorted(
                    SUPPORTED_EXTENSIONS
                )
            )
        )

    source = load_mesh(
        input_path
    )

    return process_source(
        args=args,
        source=source,
        source_name=input_path.stem,
        input_label=str(
            input_path
        ),
        demo_name=None,
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )