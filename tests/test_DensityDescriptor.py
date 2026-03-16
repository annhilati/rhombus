from Rhombus.language.density import Density, resolve_DensityDescriptor
from Rhombus.language import types

def test_resolve_DensityDescriptor():
    
    # int
    assert resolve_DensityDescriptor(1) == Density(types.constant(1.0))
    # float
    assert resolve_DensityDescriptor(4.5) == Density(types.constant(4.5))
    # large floats
    assert resolve_DensityDescriptor(1234567.0) == Density(types.mul(types.constant(1000000.0), types.constant(1.234567)))
    # str
    assert resolve_DensityDescriptor("test:reference") == Density(types.Reference("test:reference"))
    # DensityFunction
    assert resolve_DensityDescriptor(types.constant(1.0)) == Density(types.constant(1.0))