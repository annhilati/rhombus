from rhombus.std.density import Density

from . import types


def lonely_island() -> Density[types.lonely_island]:
    return Density(types.lonely_island())

def floating_islands() -> Density[types.floating_islands]:
    return Density(types.floating_islands())