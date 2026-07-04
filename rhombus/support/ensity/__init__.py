"""### [En-sityFunctions](https://modrinth.com/mod/en-sityfunction) by MikeStorm03

Provides specialized density function types for structuring the End dimension.
These functions facilitate the separation and shaping of distinct regions,
such as isolating the main central island from the surrounding outer islands.
"""
"""### [En-sityFunctions](https://modrinth.com/mod/en-sityfunction) by MikeStorm03

Provides specialized density function types for structuring the End dimension.
These functions facilitate the separation and shaping of distinct regions,
such as isolating the main central island from the surrounding outer islands.
"""

__version__ = "0.1.2"

from .functions import floating_islands, lonely_island

from importlib.resources import files as _files
from rhombus.core.config import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction
from . import types as _types

__addon__ = _RhombusAddon(
    name="Ensity",
    preview_scripts=[_files("rhombus.support.ensity").joinpath("deepslate.ts")],
    density_functions={
        cls.id: cls for name, cls in _types.__dict__.items()
        if isinstance(cls, type) and issubclass(cls, _DensityFunction) and hasattr(cls, "id")
    }
)
