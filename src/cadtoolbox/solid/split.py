def split_build123d_by_plane(shape, plane):
    """Split a build123d shape by a plane and return the backend result."""
    return shape.split(bisect_by=plane)
