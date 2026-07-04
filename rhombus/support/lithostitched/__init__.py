"""### [Lithostitched](https://modrinth.com/mod/lithostitched) by Apollo

Offers a comprehensive suite of extended density functions and utilities for advanced world generation.
This module enables finer control over terrain shaping and noise manipulation within the datapack ecosystem.

---
[Wiki](https://github.com/Apollounknowndev/lithostitched/wiki)
([Density Function Types](https://github.com/Apollounknowndev/lithostitched/wiki/Density-Function-Types), [Fast Noise Configs](https://github.com/Apollounknowndev/lithostitched/wiki/Fast-Noise-Configs))
"""

__version__ = "1.6.0"

from .functions import *
from .fast_noise_config import FastNoiseConfig, LithostitchedFastNoiseConfig

from importlib.resources import files as _files
from rhombus.core.config import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction
from . import types as _types

__addon__ = _RhombusAddon(
    name="Lithostitched",
    preview_scripts=[
        _files("rhombus.support.lithostitched").joinpath("fastnoise-lite.ts"),
        _files("rhombus.support.lithostitched").joinpath("deepslate.ts")
    ],
    preview_beet_file_extensions={LithostitchedFastNoiseConfig},
    density_functions={
        cls.id: cls for name, cls in _types.__dict__.items()
        if isinstance(cls, type) and issubclass(cls, _DensityFunction) and hasattr(cls, "id")
    }
)