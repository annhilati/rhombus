from rhombus import flat_cache, Density
from rhombus.language import types

def test_caching_factories():

    assert Density.separated(1.0) == Density(types.Reference(reference='rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', default=types.constant(argument=1.0)))
    assert Density.configured("test", 1.0) == Density(types.Reference(reference='minecraft:test', default=types.constant(argument=1.0)))

def test_caching_builtins():

    ...