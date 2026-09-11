# Architecture

## Operation first, application second

Reusable geometry behavior belongs under `src/cadtoolbox/`.
Application-specific execution belongs under `scripts/<application>`.

Prefer parametric Python as source, STEP for neutral BREP interchange, and
STL/3MF at the manufacturing boundary.
