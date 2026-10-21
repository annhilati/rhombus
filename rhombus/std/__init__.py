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
    maps,
    noise as noises,
    math,
    blending
)

# Convenience
from rhombus.std.builtin.density import Density, AnyDensity
from rhombus.std.builtin.macros import macro

from .builtin import density, macros