# Codex continuation prompt

Use this file when handing the repository to Codex.

## Goal

Continue developing this repository as a reusable cross-application CAD tooling
layer. Do not replace the architecture with app-specific piles of scripts.

## Rules

1. Preserve the operation-first layout under `src/cadtoolbox`.
2. Keep imports of optional heavy backends lazy.
3. A missing optional backend must produce a clear actionable error.
4. Do not silently mesh a BREP unless the user explicitly requested a mesh output.
5. STEP should remain the preferred neutral BREP format.
6. Mesh operations should use trimesh unless Blender is specifically required.
7. build123d is the preferred Python BREP backend for new generated geometry.
8. Keep CadQuery support because existing scripts and CQ-editor users may need it.
9. FreeCAD and Blender adapters must be usable from those applications' Python interpreters.
10. Add tests for every pure-Python behavior and for backend dispatch where feasible.
11. Never hardcode user-specific absolute filesystem paths.
12. Preserve CLI backwards compatibility once a command exists.
13. All generated artifacts go to an explicit output path or an `exports/` directory.
14. Keep functions small, typed, documented, and reusable.

## Next implementation priorities

- Add STEP assembly tree inspection when the backend exposes names/colors.
- Add DXF/SVG profile import/export adapters.
- Add BREP split-by-plane and split-by-solid helpers in build123d.
- Add STL tessellation controls to `cad convert`.
- Add model-unit metadata where source formats provide it.
- Add richer mesh diagnostics (watertight, winding, components, volume, area).
- Add named transform presets and JSON transform files.
- Add a `cad batch` subcommand for directory operations.
- Add OCP CAD Viewer / Jupyter examples for browser-first use.
- Add FreeCAD document helpers for Part/Body creation and import placement.
- Add Blender CLI wrappers for headless conversion/repair.
- Add GitHub Actions that run only unit tests and never process large CAD assets.

## Definition of done for each feature

- implementation
- CLI exposure when appropriate
- README example
- unit tests
- useful error messages
- no placeholder `pass`
