from rhombus import Density
from rhombus.std import densityfunction, vdft

def test_separating_factories():

    assert Density.partitioned(1.0) == Density(vdft.Reference(reference='rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', definition=vdft.constant(argument=1.0)))
    assert Density.configured("test", 1.0) == Density(vdft.Reference(reference='minecraft:test', definition=vdft.constant(argument=1.0)))


def test_resolve_DensityDescriptor():
    
    # int
    assert densityfunction.unify(1) == Density(vdft.constant(1.0))
    # float
    assert densityfunction.unify(4.5) == Density(vdft.constant(4.5))
    # # large floats
    # assert densityfunction.unify(1234567.0) == Density(types.mul(types.constant(1000000.0), types.constant(1.234567)))
    # str
    assert densityfunction.unify("test:reference") == Density(vdft.Reference("test:reference"))
    # DensityFunction
    assert densityfunction.unify(vdft.constant(1.0)) == Density(vdft.constant(1.0))