from pathlib import Path
from cadtoolbox.model import Model

def test_kinds():
    assert Model(Path("thing.step")).kind == "brep"
    assert Model(Path("thing.stl")).kind == "mesh"
