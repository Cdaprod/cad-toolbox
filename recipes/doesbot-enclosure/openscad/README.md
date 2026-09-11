Below is a **single, complete OpenSCAD file** you can paste in and render immediately. It gives you a parametric two-piece enclosure based on the **127 × 85.725 mm / 5 × 3⅜ in Doesbot board**, with:

- Bottom enclosure
- Removable lid
- Continuous internal locating lip
- Clearance between lip and lid
- Four PCB mounting standoffs
- Four enclosure screw bosses
- M3-style holes
- Top ventilation slots
- Bottom intake vents
- Parametric cable/connector cutouts on both long sides and the short ends
- Board reference model
- Exploded/assembled views
- Individual top/bottom STL rendering modes
- Adjustable board location
- Adjustable enclosure clearance
- Adjustable port locations
- Optional first-prototype elongated PCB mounting slots

The **only dimensions I’m deliberately not pretending to know** are the exact Doesbot mounting-hole coordinates and connector positions. Those are exposed at the top so we can tune them from your measurements.

The first thing I would do is open it in OpenSCAD and set:

```scad
PART = “exploded”;
```

Press **F5** first. You should see approximately:

```text
             ┌─────────────────────┐
             │        LID          │
             │   ////// vents      │
             └─────────────────────┘


             ┌─────────────────────┐
             │    DOESBOT PCB      │
             └─────────────────────┘


        ╭────────────────────────────╮
        │ ●                      ●   │
        │                            │
        │     mounting standoffs     │
        │                            │
        │ ●                      ●   │
        ╰────────────────────────────╯
                    BASE
```

Then use `PART = “bottom”` and **F6** for the printable lower enclosure. `PART = “top”` gives you the separately printable lid.

The most important numbers we’ll replace from your actual board are these:

```scad
PCB_HOLE_EDGE_X = 4.0;
PCB_HOLE_EDGE_Y = 4.0;
```

and the values under:

```scad
// 10. CONNECTOR / CABLE CUTOUTS
```

I deliberately made the mounting holes **slotted for the prototype**, so even if our first hole coordinates are off by a couple millimeters, there’s a decent chance the physical board will still mount. Once you give me the **center-to-center distance between the Doesbot mounting screws in X and Y**, I can make those mounting locations exact and then we can start locating each real terminal block/USB/cable exit from the photo and measurements.