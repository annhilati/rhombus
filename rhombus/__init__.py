"""The Python-embedded Domain specific Language for Minecraft Terrain Generation.

[Documentation](https://annhilati.github.io/rhombus) •
[GitHub](https://github.com/annhilati/rhombus)

It is recomment to import `*` from this module and from other module only
specific symbols to be able to make the most of the DSL experience.
"""

from rhombus.std import *
from rhombus.macros import *
from rhombus.support import *
from rhombus import (
    splines,
    preview,
)
from rhombus.config import env

from rhombus import std as _std
env.load(_std)

# Convenience when importing *
from rich import print