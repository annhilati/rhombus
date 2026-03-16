from Rhombus import flat_cache, Density
from Rhombus.language import types

def test_caching_factories():

    assert Density.separated(1.0) == Density(types.Reference(reference='rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', default=types.constant(argument=1.0)))
    assert Density.configured("test", 1.0) == Density(types.Reference(reference='minecraft:test', default=types.constant(argument=1.0)))

def test_caching_builtins():

    assert flat_cache(1.0) == Density(types.Reference(reference='rhombus:generated/c2ce730b562b7ce281e701dadc1f0ce5', default=types.flat_cache(types.constant(1.0))))