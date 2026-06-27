"""The Python-embedded Domain specific Language for Minecraft Terrain Generation.

[Documentation](https://annhilati.github.io/rhombus) •
[GitHub](https://github.com/annhilati/rhombus)
"""

from rhombus.std import *
from rhombus.macros import *
from rhombus import (
    splines,
    support,
    preview
)
from rhombus.config import env
from rhombus.config import register

register(t)
env.caching_function_types.update({t.cache_2d, t.flat_cache, t.cache_all_in_cell, t.cache_once})

# Convenience when importing *
from rich import print