"""
# The Rhombus standard library
This module contains all the symbols needed to develop vanilla terrain
generation for datapacks, as well as some tools that are generally well
suited for this purpose.
"""

__version__ = "26.2"

from rhombus.std.noise import *
from rhombus.std.macros import *
from rhombus.std.density import *
from rhombus.std.functions import *
from rhombus.std import functions as f
from rhombus.std import types as t

from rhombus.core.environment import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction
from . import types as _types

__addon__ = _RhombusAddon(
    name="StdAddon",
    density_functions={
        cls.id: cls
        for name, cls in _types.__dict__.items()
        if name in _types.__all__
        and isinstance(cls, type)
        and issubclass(cls, _DensityFunction)
        and hasattr(cls, "id")
    },
    caching_functions={t.cache_2d, t.flat_cache, t.cache_all_in_cell, t.cache_once},
)
