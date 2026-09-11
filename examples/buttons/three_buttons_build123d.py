from build123d import Align, Box, Compound, Pos, export_step

button = Box(4, 6, 2.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
assembly = Compound(children=[Pos(x,0,0)*button for x in (0,12,24)])
export_step(assembly, "three-buttons.step")
