from Rhombus import Density
from Rhombus.core import dft

def test_Density_from_dict():
    assert Density.from_dict({"type": "abs", "argument": 1.0}) == Density(dft.abs(dft.constant(1.0)))

    assert Density.from_dict({"type": "abs", "argument": "test:reference"}) == Density(dft.abs(dft.Reference("test:reference")))