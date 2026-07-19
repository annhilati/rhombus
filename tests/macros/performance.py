from rhombus.macros import performance
from rhombus.std import Density
from rhombus.core import Reference


def test_get_size_handles_reference_definitions_without_recursion():
    ref = Reference("minecraft:custom", Density(1).AST)
    size = performance.get_size(Density(ref))

    assert size.toplevel_nodes >= 1
    assert size.unique_cached_nodes == 0
    assert size.unique_unknown_references == 0
    assert size.total_unknown_references == 0
