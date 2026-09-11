def offset_build123d(shape, amount: float):
    """Thin wrapper around build123d offset when available on the supplied shape."""
    if not hasattr(shape, "offset_3d"):
        raise TypeError("shape does not expose build123d offset_3d")
    return shape.offset_3d(float(amount))
