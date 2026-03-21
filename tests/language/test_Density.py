from rhombus import Density
from rhombus.language import types, resolve_DensityDescriptor

def test_separating_factories():

    assert Density.separated(1.0) == Density(types.Reference(reference='rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', default=types.constant(argument=1.0)))
    assert Density.configured("test", 1.0) == Density(types.Reference(reference='minecraft:test', default=types.constant(argument=1.0)))


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