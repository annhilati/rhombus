"""### [En-sityFunctions](https://modrinth.com/mod/en-sityfunction) by MikeStorm03

Provides specialized density function types for structuring the End dimension.
These functions facilitate the separation and shaping of distinct regions,
such as isolating the main central island from the surrounding outer islands.
"""

__version__ = "0.1.2"

from .functions import floating_islands, lonely_island

def _register_rhombus_addon() -> None:
    from importlib.resources import files
    
    from rhombus.core.config import env
    from rhombus.core.density_function import DensityFunction
    
    from . import types

    env.preview_scripts.append(files("rhombus.support.ensity").joinpath("deepslate.ts"))
    
    env.density_function_type_deserialization_register.update({
        cls.id: cls for name, cls in types.__dict__.items()
        if isinstance(cls, type) and issubclass(cls, DensityFunction) and hasattr(cls, "id")
    })
