"""### [Lithostitched](https://modrinth.com/mod/lithostitched) by Apollo

Offers a comprehensive suite of extended density functions and utilities for advanced world generation.
This module enables finer control over terrain shaping and noise manipulation within the datapack ecosystem.

---
[Wiki](https://github.com/Apollounknowndev/lithostitched/wiki)
([Density Function Types](https://github.com/Apollounknowndev/lithostitched/wiki/Density-Function-Types), [Fast Noise Configs](https://github.com/Apollounknowndev/lithostitched/wiki/Fast-Noise-Configs))
"""

__version__ = "1.6.0"

from .functions import *
from .fast_noise_config import FastNoiseConfig, LithostichedFastNoiseConfig

def _register_rhombus_addon() -> None:
    from importlib.resources import files
    
    from rhombus.core.config import env
    from rhombus.core.density_function import DensityFunction
    
    from . import types

    env.preview_scripts.append(files("rhombus.support.lithostitched").joinpath("fastnoise-lite.ts"))
    env.preview_scripts.append(files("rhombus.support.lithostitched").joinpath("deepslate.ts"))
    
    env.density_function_type_deserialization_register.update({
        cls.id: cls for name, cls in types.__dict__.items()
        if isinstance(cls, type) and issubclass(cls, DensityFunction) and hasattr(cls, "id")
    })