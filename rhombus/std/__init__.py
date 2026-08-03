"""
# The Rhombus standard library
This module contains all the symbols needed to develop vanilla terrain
generation for datapacks, as well as some tools that are generally well
suited for this purpose.
"""

from . import (
    caching,
    conditional,
    coords,
    density,
    emath,
    macros,
    maps,
    math,
    noise,
    smath,
)

# Convenience
from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro, RhombusVersionError