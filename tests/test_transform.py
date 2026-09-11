from cadtoolbox.geometry.transform import Transform

def test_transform_translation():
    m = Transform(x=1, y=2, z=3).matrix()
    assert m[0][3] == 1
    assert m[1][3] == 2
    assert m[2][3] == 3
