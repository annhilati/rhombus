from rhombus import Density
from rhombus.language import types, densityfunction

def test_separating_factories():

    assert Density.partitioned(1.0) == Density(types.Reference(reference='rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', definition=types.constant(argument=1.0)))
    assert Density.configured("test", 1.0) == Density(types.Reference(reference='minecraft:test', definition=types.constant(argument=1.0)))


def test_resolve_DensityDescriptor():
    
    # int
    assert densityfunction.unify(1) == Density(types.constant(1.0))
    # float
    assert densityfunction.unify(4.5) == Density(types.constant(4.5))
    # large floats
    assert densityfunction.unify(1234567.0) == Density(types.mul(types.constant(1000000.0), types.constant(1.234567)))
    # str
    assert densityfunction.unify("test:reference") == Density(types.Reference("test:reference"))
    # DensityFunction
    assert densityfunction.unify(types.constant(1.0)) == Density(types.constant(1.0))