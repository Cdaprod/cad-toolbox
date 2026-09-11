from build123d import import_step

MODEL = "raspberry-pi-5.step"
shape = import_step(MODEL)
bb = shape.bounding_box()
print("size:", bb.size)
