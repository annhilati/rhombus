"""### [En-sityFunctions](https://modrinth.com/mod/en-sityfunction) by MikeStorm03

Provides specialized density function types for structuring the End dimension.
These functions facilitate the separation and shaping of distinct regions,
such as isolating the main central island from the surrounding outer islands.
"""

from .functions import floating_islands, lonely_island
from . import types

from rhombus.core.environment import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction

__addon__ = _RhombusAddon(
    namespace="ensity",
    version=(0, 1, 2),
    preview_scripts=[_RhombusAddon.resource("rhombus.support.ensity", "deepslate.ts")],
    density_functions={
        cls.id: cls
        for name, cls in types.__dict__.items()
        if isinstance(cls, type)
        and issubclass(cls, _DensityFunction)
        and hasattr(cls, "id")
    },
)
