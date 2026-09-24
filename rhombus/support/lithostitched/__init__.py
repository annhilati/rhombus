"""### [Lithostitched](https://modrinth.com/mod/lithostitched) by Apollo

Offers a comprehensive suite of extended density functions and utilities for advanced world generation.
This module enables finer control over terrain shaping and noise manipulation within the datapack ecosystem.

---
[Wiki](https://github.com/Apollounknowndev/lithostitched/wiki)
([Density Function Types](https://github.com/Apollounknowndev/lithostitched/wiki/Density-Function-Types), [Fast Noise Configs](https://github.com/Apollounknowndev/lithostitched/wiki/Fast-Noise-Configs))
"""

from .functions import *
from .fast_noise_config import FastNoiseConfig, LithostitchedFastNoiseConfig
from . import types

from rhombus.core.environment import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction

__addon__ = _RhombusAddon(
    namespace="lithostitched",
    version=(1, 6, 0),
    preview_scripts=[
        _RhombusAddon.resource("rhombus.support.lithostitched", "fastnoise-lite.ts"),
        _RhombusAddon.resource("rhombus.support.lithostitched", "deepslate.ts"),
    ],
    preview_beet_file_extensions={LithostitchedFastNoiseConfig},
    density_functions={
        cls.id: cls
        for name, cls in types.__dict__.items()
        if isinstance(cls, type)
        and issubclass(cls, _DensityFunction)
        and hasattr(cls, "id")
    },
)
