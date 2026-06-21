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

# Convenience when importing *
from rich import print