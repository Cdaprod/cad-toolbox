from build123d import Align, Box, export_step

outer = Box(100, 70, 30, align=(Align.CENTER, Align.CENTER, Align.MIN))
inner = Box(95, 65, 28, align=(Align.CENTER, Align.CENTER, Align.MIN))
enclosure = outer - inner
export_step(enclosure, "simple-enclosure.step")
