from cadtoolbox.geometry.units import inch_to_mm, mm_to_inch

def test_units():
    assert inch_to_mm(1) == 25.4
    assert mm_to_inch(25.4) == 1
