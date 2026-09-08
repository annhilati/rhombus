from rhombus.std.density import Density

from . import types


def lonely_island() -> Density:
    "Returns a density function that features just the main End island."
    return Density(types.lonely_island())


def floating_islands() -> Density:
    "Returns a density function that features just the outer End islands."
    return Density(types.floating_islands())
