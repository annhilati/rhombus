from Rhombus import Density
from Rhombus.core import dft

def test_Density_from_dict():
    
    # literal constants
    assert Density.from_dict({"type": "abs", "argument": 1.0}) == Density(dft.abs(dft.constant(1.0)))
    # nested functions
    assert Density.from_dict({"type": "abs", "argument": {"type": "abs", "argument": 1.0}}) == Density(dft.abs(dft.abs(dft.constant(1.0))))
    # literal references
    assert Density.from_dict({"type": "abs", "argument": "test:reference"}) == Density(dft.abs(dft.Reference("test:reference")))