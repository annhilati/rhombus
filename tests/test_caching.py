from Rhombus import flat_cache, Density, ExternalDensity, ConfiguredDensity
from Rhombus.core import dft

def test_caching_factories():

    assert ExternalDensity(1.0) == Density(dft.Reference(reference='rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', default=dft.constant(argument=1.0)))
    assert ConfiguredDensity("test", 1.0) == Density(dft.Reference(reference='minecraft:test', default=dft.constant(argument=1.0)))

def test_caching_builtins():

    assert flat_cache(1.0) == Density(dft.Reference(reference='rhombus:generated/c2ce730b562b7ce281e701dadc1f0ce5', default=dft.flat_cache(dft.constant(1.0))))