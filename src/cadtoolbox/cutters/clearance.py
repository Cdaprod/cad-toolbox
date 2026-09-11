def bilateral(nominal: float, clearance: float) -> float:
    """Apply clearance to both sides of a linear dimension."""
    return float(nominal) + 2.0 * float(clearance)

def radial(nominal_diameter: float, clearance: float) -> float:
    """Apply radial clearance to a diameter."""
    return float(nominal_diameter) + 2.0 * float(clearance)
