"""The Python-embedded Domain specific Language for Minecraft Terrain Generation.

[Documentation](https://annhilati.github.io/rhombus) •
[GitHub](https://github.com/annhilati/rhombus)
"""

from rhombus.std import *
from rhombus.macros import *
from rhombus import (
    splines,
    support,
    preview,
    std
)
from rhombus.config import env

env.load(std)

# Convenience when importing *
from rich import print