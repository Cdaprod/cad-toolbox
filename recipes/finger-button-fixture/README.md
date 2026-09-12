# Parametric Finger Button Fixture Recipe

Reusable near-flush finger-button fixture for the camera-grip project.

The intent is to define **one mechanical button stack** and reuse it for the
index, middle, and ring finger faces.

The fixture generates four coordinated solids:

```text
ButtonFixture
├── cap         printable moving cap
├── switch_ref  actual 6 x 4 x 2.5 mm switch envelope
├── board_ref   nominal 10 x 12 x 1 mm perfboard
└── cutter      stepped Boolean relief body
```

## Mechanical model

Local `+Z` points **out of the grip**.

```text
                         OUTSIDE
                            +Z

                      ┌─────────────┐
                      │  cap face   │
                      └──────┬──────┘
─────────────────────────────┼──────────── grip skin
                    ┌────────┴────────┐
                    │ hidden flange   │
                    └────────┬────────┘
                             │ stem
                             │
                         ┌───────┐
                         │switch │
                         └───────┘
                      ┌─────────────┐
                      │  perfboard  │
                      └─────────────┘
                       solder/wires

                            -Z
                          INSIDE
```

The hidden flange is wider than the cap opening, so the cap cannot pop out
through the grip.

The cutter is intentionally larger than the physical parts. It creates:

1. cap opening,
2. flange travel relief,
3. stem travel,
4. switch body clearance,
5. perfboard pocket,
6. rear solder/wire relief.

## Install

From the root of `Cdaprod/cad-toolbox`:

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -r recipes/finger-button-fixture/requirements.txt
```

## Generate the fixture

```bash
python recipes/finger-button-fixture/generate_fixture.py
```

Outputs:

```text
build/finger-button-fixture/
├── finger_button_cap.step
├── finger_button_cap.stl
├── finger_button_switch_ref.step
├── finger_button_switch_ref.stl
├── finger_button_board_ref.step
├── finger_button_board_ref.stl
├── finger_button_cutter.step
├── finger_button_cutter.stl
└── finger_button_params.json
```

Open those STEP files in FreeCAD, Onshape, or your other CAD tool and verify the
dimensions before touching the real grip.

## Override dimensions

Example using a 10 x 10 mm button board:

```bash
python recipes/finger-button-fixture/generate_fixture.py \
  --switch-x 6 \
  --switch-y 4 \
  --switch-z 2.5 \
  --board-x 10 \
  --board-y 10 \
  --board-z 1 \
  --cap-x 13 \
  --cap-y 11 \
  --cap-z 1.8 \
  --flange-overhang 0.8 \
  --cap-clearance 0.25
```

See all supported parameters:

```bash
python recipes/finger-button-fixture/generate_fixture.py --help
```

## Apply it to the grip three times

First edit:

```text
recipes/finger-button-fixture/placements.json
```

Each finger gets:

```json
{
  "name": "index",
  "x": 0.0,
  "y": 0.0,
  "z": 0.0,
  "rx": 0.0,
  "ry": 0.0,
  "rz": 0.0
}
```

Coordinates are millimeters; rotations are degrees.

Then run:

```bash
python recipes/finger-button-fixture/apply_to_grip.py \
  path/to/Camera_Right_Grip.step \
  --preview
```

The `--preview` option first exports transformed reference bodies for every
finger:

```text
build/finger-button-fixture/placement-preview/
├── index_cap.step
├── index_switch.step
├── index_board.step
├── index_cutter.step
├── middle_cap.step
├── ...
└── ring_cutter.step
```

Inspect those against the grip before trusting the Boolean.

The final Boolean result is:

```text
build/finger-button-fixture/grip_with_finger_buttons.step
```

## Placement workflow

Do not initially try to calculate perfect placements from code.

Use this loop:

```text
generate fixture
      ↓
edit placements.json
      ↓
run with --preview
      ↓
inspect STEP in FreeCAD/Onshape
      ↓
adjust XYZ / rotation
      ↓
repeat
      ↓
Boolean-cut final grip
```

This is deliberate. It makes placement data small, readable, Git-diffable, and
easy to tune from the iPhone/SSH workflow without destructively editing the
grip.

## Default dimensions

```text
switch        6.0 x 4.0 x 2.5 mm
board        10.0 x 12.0 x 1.0 mm
cap          13.0 x 11.0 x 1.8 mm
flange        +0.8 mm each side
flange depth   1.0 mm
stem           4.0 x 4.0 x 2.0 mm

cap XY clearance       0.25 mm / side
switch XY clearance    0.30 mm / side
board XY clearance     0.40 mm / side
```

These are starting values for FDM prototypes, not universal production
tolerances.

## Why the cutter is separate

Do **not** subtract the exact switch or exact perfboard model from the grip.

Physical reference geometry answers:

> Where does the hardware exist?

Cutter geometry answers:

> How much material must be removed so the hardware can actually fit,
> move, assemble, and tolerate print error?

Keeping those concerns separate prevents the CAD model from becoming a set of
zero-clearance Boolean operations.

## Future extension

This recipe is intentionally ready to grow into surface-normal placement.

The next useful improvement is a helper that takes:

```text
face + UV point
```

or

```text
surface point + surface normal + tangent
```

and derives the placement automatically:

```text
local Z = outward face normal
local X = fingertip-width direction
local Y = along-finger direction
```

That would let the same cutter conform naturally to three different curved
finger faces without hand-entering Euler angles.
