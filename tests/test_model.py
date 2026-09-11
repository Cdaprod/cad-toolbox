from pathlib import Path
from cadtoolbox.model import Model

def test_model_kind():
    assert Model(Path("x.step")).kind == "brep"
    assert Model(Path("x.stl")).kind == "mesh"
    assert Model(Path("x.dxf")).kind == "profile"
    assert Model(Path("x.scad")).kind == "source"
