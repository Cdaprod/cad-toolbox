from build123d import Box, Compound, Pos, export_step

BUTTON_W = 4.0
BUTTON_D = 6.0
BUTTON_H = 2.5
SPACING = 12.0

button = Box(BUTTON_W, BUTTON_D, BUTTON_H)
buttons = Compound(children=[
    Pos(0, 0, 0) * button,
    Pos(SPACING, 0, 0) * button,
    Pos(SPACING * 2, 0, 0) * button,
])
export_step(buttons, "three-buttons.step")
