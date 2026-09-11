def fillet_build123d(shape, radius: float, edges):
    from build123d import fillet
    return fillet(edges, radius=float(radius))
