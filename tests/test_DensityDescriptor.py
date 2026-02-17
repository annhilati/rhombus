from Rhombus.language.density import Density, resolve_DensityDescriptor
from Rhombus.core import dft

def test_resolve_DensityDescriptor():
    
    # int
    assert resolve_DensityDescriptor(1) == Density(dft.constant(1.0))
    # float
    assert resolve_DensityDescriptor(4.5) == Density(dft.constant(4.5))
    # large floats
    assert resolve_DensityDescriptor(1234567.0) == Density(dft.mul(dft.constant(1000000.0), dft.constant(1.234567)))
    # str
    assert resolve_DensityDescriptor("test:reference") == Density(dft.Reference("test:reference"))
    # DensityFunction
    assert resolve_DensityDescriptor(dft.constant(1.0)) == Density(dft.constant(1.0))