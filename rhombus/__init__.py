"""The Python embedded DSL for writing Density Functions for Minecraft Datapacks

[Documentation](https://annhilati.github.io/rhombus)

[GitHub](https://github.com/annhilati/rhombus)
"""

from rhombus.std import *
from rhombus.macros import *
from rhombus import (
    config,
    splines,
    support
)
from rhombus.core.density_function import register

register(t)

# Convenience when importing *
from rich import print