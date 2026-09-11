from build123d import Align, Box, Cylinder, Pos, export_step

plate = Box(70, 70, 6, align=(Align.CENTER, Align.CENTER, Align.MIN))
for x in (-23.5, 23.5):
    for y in (-23.5, 23.5):
        plate -= Pos(x, y, -0.2) * Cylinder(2.75, 6.4, align=(Align.CENTER,Align.CENTER,Align.MIN))
export_step(plate, "motor-mount-pattern.step")
