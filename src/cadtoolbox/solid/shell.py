def shell_build123d(shape, thickness: float, openings=None):
    from build123d import offset
    openings = [] if openings is None else openings
    return offset(shape, amount=float(thickness), openings=openings)
