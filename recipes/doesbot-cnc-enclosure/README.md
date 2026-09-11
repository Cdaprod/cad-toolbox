# Doesbot CNC controller enclosure

Parametric build123d rewrite of the original OpenSCAD enclosure.

Run:

```bash
python recipes/doesbot-cnc-enclosure/doesbot_enclosure.py
```

Outputs STEP + STL to `exports/`.

The geometry is intentionally parameter-driven and should be updated from actual
PCB mounting-hole and connector measurements before printing.
