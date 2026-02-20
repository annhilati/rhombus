from Rhombus import Density, Noise
from Rhombus.support.builtin import dft

def test_Density_from_dict():
    
    # literal constants
    assert Density.from_dict({"type": "abs", "argument": 1.0}) == Density(dft.abs(dft.constant(1.0)))
    
    # nested functions
    assert Density.from_dict({"type": "abs", "argument": {"type": "abs", "argument": 1.0}}) == Density(dft.abs(dft.abs(dft.constant(1.0))))

    # literal references
    assert Density.from_dict({"type": "abs", "argument": "test:reference"}) == Density(dft.abs(dft.Reference("test:reference")))

    # RegistryResources
    assert Density.from_dict({"type": "noise", "noise": "referenced:noise", "xz_scale": 1, "y_scale": 1}) == Density(dft.noise(noise=Noise(None, None, reference='referenced:noise'), xz_scale=1, y_scale=1))