"""Provides backward compatibility for Minecraft world generation features that have been altered or removed.

This module restores legacy density functions and noise types to maintain compatibility with older world designs.
When importing from this module, ensure it is done after importing standard symbols to avoid conflicts.
"""

from .functions import *
from . import types

from rhombus.core.config import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction

__addon__ = _RhombusAddon(
    name="VanillaLegacy",
    density_functions={
        cls.id: cls for name, cls in types.__dict__.items()
        if isinstance(cls, type) and issubclass(cls, _DensityFunction) and hasattr(cls, "id")
    }
)