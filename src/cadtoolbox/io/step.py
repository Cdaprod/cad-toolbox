def import_build123d(path):
    from build123d import import_step
    return import_step(str(path))

def export_build123d(shape, path):
    from build123d import export_step
    export_step(shape, str(path))
