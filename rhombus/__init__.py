"""The Python-embedded Domain specific Language for Minecraft Terrain Generation.

[Documentation](https://annhilati.github.io/rhombus) •
[GitHub](https://github.com/annhilati/rhombus)
"""

from rhombus.std import *
from rhombus.macros import *
from rhombus import (
    config,
    splines,
    support,
    preview
)
from rhombus.core.density_function import register

register(t)
config.ctx.caching_function_types.set(frozenset([t.cache_2d, t.flat_cache, t.cache_all_in_cell, t.cache_once]))

# Convenience when importing *
from rich import print