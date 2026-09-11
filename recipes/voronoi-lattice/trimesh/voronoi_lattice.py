#!/usr/bin/env python3
"""
Generate a printable 3D Voronoi strut lattice clipped to an arbitrary watertight mesh.

Default workflow:
    python3 voronoi_lattice.py path/to/model.stl

Help:
    python3 voronoi_lattice.py --help

The script:
  1. Loads STL/OBJ/PLY/GLB/GLTF/3MF via trimesh.
  2. Samples seed points inside the solid.
  3. Computes a 3D SciPy Voronoi diagram.
  4. Converts finite Voronoi ridge edges into cylindrical struts.
  5. Adds spherical node joints.
  6. Uses manifold3d through trimesh to union and clip the lattice to the source solid.
  7. Overwrites stable output names on every run so changed parameters update results.
  8. Writes STL, GLB, and a JSON manifest containing the effective parameters.

Dependencies:
    python3 -m pip install numpy scipy trimesh rtree manifold3d

Notes:
  - The input should be a closed/watertight solid for reliable volume sampling and clipping.
  - "Preview" mode skips booleans and is much faster, but the result can contain
    overlapping struts and extend slightly outside the source model.
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
from typing import Iterable

import numpy as np
from scipy.spatial import Voronoi
import trimesh


SUPPORTED_EXTENSIONS = {".stl", ".obj", ".ply", ".glb", ".gltf", ".3mf"}


@dataclass
class EffectiveConfig:
    input: str
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
    repair: bool
    source_extents_mm: list[float]
    source_diagonal_mm: float


def warn(message: str) -> None:
    print(f"[guardrail] {message}", file=sys.stderr)


def require_runtime_dependencies(*, preview_only: bool) -> None:
    missing: list[str] = []

    # trimesh volume sampling / contains_points needs an R-tree spatial index.
    if importlib.util.find_spec("rtree") is None:
        missing.append("rtree")

    # Printable mode performs robust mesh union + intersection through manifold3d.
    if not preview_only and importlib.util.find_spec("manifold3d") is None:
        missing.append("manifold3d")

    if missing:
        packages = " ".join(missing)
        mode_note = (
            "\nFor a quick non-printable result, --preview-only avoids manifold3d."
            if "manifold3d" in missing
            else ""
        )
        raise RuntimeError(
            "Missing runtime dependency/dependencies: "
            + ", ".join(missing)
            + "\nInstall with:\n"
            + f"  python3 -m pip install {packages}"
            + mode_note
        )


def clamp(value: float, low: float, high: float, label: str) -> float:
    if value < low:
        warn(f"{label} {value:g} is too small; using {low:g}.")
        return low
    if value > high:
        warn(f"{label} {value:g} is too large; using {high:g}.")
        return high
    return value


def clamp_int(value: int, low: int, high: int, label: str) -> int:
    if value < low:
        warn(f"{label} {value} is too small; using {low}.")
        return low
    if value > high:
        warn(f"{label} {value} is too large; using {high}.")
        return high
    return value


def load_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="scene")

    if isinstance(loaded, trimesh.Trimesh):
        mesh = loaded.copy()
    elif isinstance(loaded, trimesh.Scene):
        meshes: list[trimesh.Trimesh] = []
        for geometry in loaded.geometry.values():
            if isinstance(geometry, trimesh.Trimesh):
                meshes.append(geometry.copy())
        if not meshes:
            raise ValueError(f"No mesh geometry found in {path}")
        mesh = trimesh.util.concatenate(meshes)
    else:
        raise TypeError(f"Unsupported geometry type: {type(loaded).__name__}")

    mesh.remove_unreferenced_vertices()
    return mesh


def try_repair(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    repaired = mesh.copy()
    try:
        trimesh.repair.fix_normals(repaired, multibody=True)
    except Exception:
        pass
    try:
        trimesh.repair.fill_holes(repaired)
    except Exception:
        pass
    repaired.remove_unreferenced_vertices()
    return repaired


def volume_sample(mesh: trimesh.Trimesh, count: int, rng: np.random.Generator) -> np.ndarray:
    """
    Sample points inside mesh. trimesh.sample.volume_mesh uses rejection sampling.
    Retry in batches because complex/thin shapes can return fewer points than requested.
    """
    collected: list[np.ndarray] = []
    total = 0

    # Make trimesh's use of NumPy's legacy RNG deterministic enough for repeatable runs.
    np.random.seed(int(rng.integers(0, 2**31 - 1)))

    for _ in range(12):
        need = count - total
        if need <= 0:
            break
        batch_request = max(need * 3, 64)
        pts = trimesh.sample.volume_mesh(mesh, batch_request)
        if len(pts):
            if len(pts) > need:
                choose = rng.choice(len(pts), size=need, replace=False)
                pts = pts[choose]
            collected.append(np.asarray(pts, dtype=float))
            total += len(pts)

    if not collected:
        raise RuntimeError(
            "Could not sample any points inside the model. "
            "The source mesh likely isn't a closed/watertight volume."
        )

    points = np.vstack(collected)
    if len(points) < count:
        warn(
            f"Requested {count} interior seeds but only found {len(points)}. "
            "Continuing with the available points."
        )
    return points[:count]


def guard_points(bounds: np.ndarray, margin: float, grid: int) -> np.ndarray:
    """
    Add a sparse box of points outside the model. These make most Voronoi cells
    around the real interior seeds finite, avoiding infinite ridge edges.
    """
    bmin = bounds[0] - margin
    bmax = bounds[1] + margin
    axes = [np.linspace(bmin[i], bmax[i], grid) for i in range(3)]

    pts: list[tuple[float, float, float]] = []

    # Six faces of an expanded bounding box.
    for y in axes[1]:
        for z in axes[2]:
            pts.append((bmin[0], y, z))
            pts.append((bmax[0], y, z))
    for x in axes[0]:
        for z in axes[2]:
            pts.append((x, bmin[1], z))
            pts.append((x, bmax[1], z))
    for x in axes[0]:
        for y in axes[1]:
            pts.append((x, y, bmin[2]))
            pts.append((x, y, bmax[2]))

    arr = np.asarray(pts, dtype=float)
    # Remove duplicated edge/corner points.
    arr = np.unique(np.round(arr, decimals=9), axis=0)
    return arr


def edge_key(a: np.ndarray, b: np.ndarray, quant: float) -> tuple:
    qa = tuple(np.round(a / quant).astype(np.int64))
    qb = tuple(np.round(b / quant).astype(np.int64))
    return (qa, qb) if qa <= qb else (qb, qa)


def voronoi_segments(
    interior: np.ndarray,
    guards: np.ndarray,
    *,
    min_length: float,
    max_length: float,
    quantization: float,
) -> list[tuple[np.ndarray, np.ndarray]]:
    points = np.vstack([interior, guards])
    vor = Voronoi(points)
    interior_count = len(interior)

    segments: dict[tuple, tuple[np.ndarray, np.ndarray]] = {}

    for sites, ridge_vertex_ids in zip(vor.ridge_points, vor.ridge_vertices):
        # Ignore ridges formed only by outside guard points.
        if sites[0] >= interior_count and sites[1] >= interior_count:
            continue

        # Infinite ridge.
        if len(ridge_vertex_ids) < 2 or -1 in ridge_vertex_ids:
            continue

        poly = vor.vertices[np.asarray(ridge_vertex_ids, dtype=int)]
        if not np.isfinite(poly).all():
            continue

        # scipy gives polygon vertices around the ridge. Join consecutive vertices
        # and close the polygon. Shared edges are deduplicated below.
        for i in range(len(poly)):
            a = poly[i]
            b = poly[(i + 1) % len(poly)]
            length = float(np.linalg.norm(b - a))
            if length < min_length or length > max_length:
                continue
            key = edge_key(a, b, quantization)
            segments.setdefault(key, (a, b))

    return list(segments.values())


def reduce_segments(
    segments: list[tuple[np.ndarray, np.ndarray]],
    max_struts: int,
    rng: np.random.Generator,
) -> list[tuple[np.ndarray, np.ndarray]]:
    if len(segments) <= max_struts:
        return segments

    warn(
        f"Voronoi produced {len(segments)} struts; limiting to {max_struts} "
        "to keep booleans and memory bounded."
    )
    ids = np.sort(rng.choice(len(segments), size=max_struts, replace=False))
    return [segments[i] for i in ids]


def build_lattice_pieces(
    segments: Iterable[tuple[np.ndarray, np.ndarray]],
    *,
    strut_radius: float,
    node_radius: float,
    cylinder_sections: int,
    node_subdivisions: int,
) -> list[trimesh.Trimesh]:
    pieces: list[trimesh.Trimesh] = []
    nodes: dict[tuple[int, int, int], np.ndarray] = {}
    quant = max(strut_radius * 0.2, 1e-6)

    for a, b in segments:
        if np.linalg.norm(b - a) <= 1e-9:
            continue

        cyl = trimesh.creation.cylinder(
            radius=strut_radius,
            segment=np.vstack([a, b]),
            sections=cylinder_sections,
        )
        pieces.append(cyl)

        for p in (a, b):
            key = tuple(np.round(p / quant).astype(np.int64))
            nodes.setdefault(key, p)

    for point in nodes.values():
        sphere = trimesh.creation.icosphere(
            subdivisions=node_subdivisions,
            radius=node_radius,
        )
        sphere.apply_translation(point)
        pieces.append(sphere)

    return pieces


def union_chunked(
    meshes: list[trimesh.Trimesh],
    *,
    chunk_size: int = 120,
) -> trimesh.Trimesh:
    if not meshes:
        raise RuntimeError("No lattice pieces were generated.")

    def union_group(group: list[trimesh.Trimesh]) -> trimesh.Trimesh:
        if len(group) == 1:
            return group[0]
        result = trimesh.boolean.union(group, engine="manifold", check_volume=False)
        if result is None:
            raise RuntimeError("manifold boolean union returned no geometry.")
        if isinstance(result, list):
            result = trimesh.util.concatenate(result)
        return result

    current = meshes
    while len(current) > 1:
        next_round: list[trimesh.Trimesh] = []
        for start in range(0, len(current), chunk_size):
            next_round.append(union_group(current[start:start + chunk_size]))
        current = next_round
    return current[0]


def intersect_with_source(
    lattice: trimesh.Trimesh,
    source: trimesh.Trimesh,
) -> trimesh.Trimesh:
    result = trimesh.boolean.intersection(
        [lattice, source],
        engine="manifold",
        check_volume=False,
    )
    if result is None:
        raise RuntimeError("manifold intersection returned no geometry.")
    if isinstance(result, list):
        result = trimesh.util.concatenate(result)
    return result


def export_outputs(
    mesh: trimesh.Trimesh,
    output_dir: Path,
    output_name: str,
    config: EffectiveConfig,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    stl_path = output_dir / f"{output_name}-voronoi-lattice.stl"
    glb_path = output_dir / f"{output_name}-voronoi-lattice.glb"
    json_path = output_dir / f"{output_name}-voronoi-lattice.json"

    # Stable names: rerunning with changed parameters updates/replaces these files.
    mesh.export(stl_path)
    mesh.export(glb_path)

    manifest = asdict(config)
    manifest["generated_unix_time"] = time.time()
    manifest["vertices"] = int(len(mesh.vertices))
    manifest["faces"] = int(len(mesh.faces))
    manifest["watertight"] = bool(mesh.is_watertight)

    json_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print("\nGenerated Voronoi lattice:")
    print(f"  STL:       {stl_path.resolve()}")
    print(f"  GLB:       {glb_path.resolve()}")
    print(f"  Manifest:  {json_path.resolve()}")
    print(f"  Vertices:  {len(mesh.vertices):,}")
    print(f"  Faces:     {len(mesh.faces):,}")
    print(f"  Watertight:{' yes' if mesh.is_watertight else ' no'}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Turn a closed mesh solid into a clipped 3D Voronoi strut lattice. "
            "Defaults are intentionally conservative for repeatable CAD-toolbox use."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input mesh: STL, OBJ, PLY, GLB, GLTF, or 3MF.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Destination directory. Default: "
            "exports/voronoi-lattice/<input-stem>/"
        ),
    )
    parser.add_argument(
        "--output-name",
        default=None,
        help="Base filename. Default: input filename without extension.",
    )

    parser.add_argument(
        "--seeds",
        type=int,
        default=85,
        help=(
            "Interior Voronoi seed count. Fewer = larger cells; "
            "more = finer/denser cellular structure. Guardrailed to 12..400."
        ),
    )
    parser.add_argument(
        "--strut-radius",
        type=float,
        default=None,
        metavar="MM",
        help=(
            "Voronoi strut radius in model units/mm. "
            "Default: 1.15%% of the model's smallest axis."
        ),
    )
    parser.add_argument(
        "--node-scale",
        type=float,
        default=1.12,
        help=(
            "Node sphere radius divided by strut radius. "
            "Guardrailed to 1.0..1.8."
        ),
    )
    parser.add_argument(
        "--guard-margin",
        type=float,
        default=None,
        metavar="MM",
        help=(
            "Distance of the helper Voronoi boundary box outside the source. "
            "Default: 18%% of the source diagonal."
        ),
    )
    parser.add_argument(
        "--guard-grid",
        type=int,
        default=3,
        help="Points per axis on each helper boundary-box face; guardrailed to 2..5.",
    )
    parser.add_argument(
        "--max-struts",
        type=int,
        default=1800,
        help=(
            "Safety cap on generated Voronoi struts. "
            "Guardrailed to 100..5000."
        ),
    )
    parser.add_argument(
        "--quality",
        choices=("low", "medium", "high"),
        default="medium",
        help="Cylinder/node tessellation quality.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Deterministic random seed. Change this to regenerate the pattern.",
    )

    parser.add_argument(
        "--preview-only",
        action="store_true",
        help=(
            "Skip boolean union/clipping. Much faster, but overlapping geometry "
            "can extend outside the source and may not be printable."
        ),
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Attempt basic normal/hole repair before sampling.",
    )

    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()

    require_runtime_dependencies(preview_only=bool(args.preview_only))

    input_path: Path = args.input.expanduser().resolve()
    if not input_path.exists():
        parser.error(f"Input does not exist: {input_path}")
    if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        parser.error(
            f"Unsupported extension {input_path.suffix!r}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    output_name = args.output_name or input_path.stem
    output_dir = (
        args.output_dir.expanduser()
        if args.output_dir is not None
        else Path("exports") / "voronoi-lattice" / input_path.stem
    )

    source = load_mesh(input_path)
    if args.repair:
        source = try_repair(source)

    extents = np.asarray(source.extents, dtype=float)
    if np.any(~np.isfinite(extents)) or np.any(extents <= 0):
        raise RuntimeError(f"Invalid source extents: {extents}")

    diagonal = float(np.linalg.norm(extents))
    min_extent = float(np.min(extents))

    seeds = clamp_int(args.seeds, 12, 400, "seeds")
    guard_grid = clamp_int(args.guard_grid, 2, 5, "guard-grid")
    max_struts = clamp_int(args.max_struts, 100, 5000, "max-struts")
    node_scale = clamp(args.node_scale, 1.0, 1.8, "node-scale")

    # Dynamic model-scale guardrails.
    min_radius = max(min_extent * 0.0015, 0.05)
    max_radius = max(min_extent * 0.08, min_radius)
    default_radius = min_extent * 0.0115
    strut_radius = clamp(
        default_radius if args.strut_radius is None else args.strut_radius,
        min_radius,
        max_radius,
        "strut-radius",
    )
    node_radius = strut_radius * node_scale

    min_guard = diagonal * 0.04
    max_guard = diagonal * 0.75
    default_guard = diagonal * 0.18
    guard_margin = clamp(
        default_guard if args.guard_margin is None else args.guard_margin,
        min_guard,
        max_guard,
        "guard-margin",
    )

    quality_map = {
        "low": (6, 1),
        "medium": (10, 1),
        "high": (16, 2),
    }
    cylinder_sections, node_subdivisions = quality_map[args.quality]

    if not source.is_watertight:
        message = (
            "Source mesh is not watertight. 3D volume sampling and boolean clipping "
            "need a closed solid."
        )
        if args.preview_only:
            warn(message + " Preview mode will still be attempted.")
        else:
            raise RuntimeError(
                message
                + " Try --repair, fix the model, or use --preview-only for a non-printable preview."
            )

    rng = np.random.default_rng(args.random_seed)

    print("Voronoi lattice configuration:")
    print(f"  Input:          {input_path}")
    print(f"  Extents:        {extents[0]:.3f} x {extents[1]:.3f} x {extents[2]:.3f}")
    print(f"  Seeds:          {seeds}")
    print(f"  Strut radius:   {strut_radius:.3f}")
    print(f"  Node radius:    {node_radius:.3f}")
    print(f"  Guard margin:   {guard_margin:.3f}")
    print(f"  Quality:        {args.quality}")
    print(f"  Random seed:    {args.random_seed}")
    print(f"  Preview only:   {args.preview_only}")

    interior = volume_sample(source, seeds, rng)
    guards = guard_points(source.bounds, guard_margin, guard_grid)

    min_segment = max(strut_radius * 1.5, diagonal * 0.001)
    max_segment = diagonal * 0.80
    quantization = max(strut_radius * 0.12, diagonal * 1e-6)

    segments = voronoi_segments(
        interior,
        guards,
        min_length=min_segment,
        max_length=max_segment,
        quantization=quantization,
    )
    if not segments:
        raise RuntimeError(
            "No finite Voronoi struts were generated. "
            "Try increasing --seeds or --guard-grid."
        )

    segments = reduce_segments(segments, max_struts, rng)
    print(f"  Voronoi struts: {len(segments)}")

    pieces = build_lattice_pieces(
        segments,
        strut_radius=strut_radius,
        node_radius=node_radius,
        cylinder_sections=cylinder_sections,
        node_subdivisions=node_subdivisions,
    )
    print(f"  Mesh pieces:    {len(pieces)}")

    if args.preview_only:
        result = trimesh.util.concatenate(pieces)
    else:
        try:
            lattice = union_chunked(pieces)
            result = intersect_with_source(lattice, source)
        except BaseException as exc:
            if exc.__class__.__name__ == "ModuleNotFoundError" or "manifold" in str(exc).lower():
                raise RuntimeError(
                    "Printable mode requires manifold3d. Install with:\n"
                    "  python3 -m pip install manifold3d\n"
                    "Or rerun with --preview-only."
                ) from exc
            raise

    result.remove_unreferenced_vertices()

    config = EffectiveConfig(
        input=str(input_path),
        output_dir=str(output_dir),
        output_name=output_name,
        seeds=seeds,
        strut_radius_mm=float(strut_radius),
        node_radius_mm=float(node_radius),
        guard_margin_mm=float(guard_margin),
        guard_grid=guard_grid,
        quality=args.quality,
        cylinder_sections=cylinder_sections,
        max_struts=max_struts,
        random_seed=args.random_seed,
        preview_only=bool(args.preview_only),
        repair=bool(args.repair),
        source_extents_mm=[float(x) for x in extents],
        source_diagonal_mm=diagonal,
    )

    export_outputs(result, output_dir, output_name, config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
