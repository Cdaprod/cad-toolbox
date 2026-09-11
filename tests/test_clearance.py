from cadtoolbox.cutters.clearance import bilateral, radial

def test_clearance():
    assert bilateral(10, 0.25) == 10.5
    assert radial(3, 0.2) == 3.4
