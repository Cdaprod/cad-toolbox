# Architecture

`cad-toolbox` treats Blender, FreeCAD, build123d, CadQuery and OpenSCAD as
backends rather than as separate universes.

```text
CLI / recipes / scripts
        |
        v
 reusable operations
        |
        +---- mesh --------> trimesh / Blender
        |
        +---- BREP --------> build123d / CadQuery / FreeCAD
        |
        +---- CSG ---------> OpenSCAD
```

## Source-of-truth preference

1. Python/build123d source for generated mechanical geometry
2. STEP for neutral BREP interchange
3. native app files when app-specific behavior matters
4. STL/3MF at the manufacturing boundary

## Why lazy imports

Blender's `bpy`, FreeCAD's Python modules, CadQuery and build123d are not always
installed in the same interpreter. Optional backend imports therefore happen
inside functions.

## Why operation-first

A "repair mesh" function should not live in a Blender repository if it can be
performed by a generic mesh engine. Application-specific wrappers stay thin.
