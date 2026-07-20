"""### [Tectonic](https://modrinth.com/datapack/tectonic) by Apollo

Exposes custom density functions and configuration nodes utilized by the Tectonic world generation mod.
This allows for seamless integration and modification of Tectonic's distinctive terrain features.
"""

from .functions import invert, config_noise, config_constant

__version__ = "3.0.19"

from importlib.resources import files as _files
from rhombus.core.environment import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction
from . import types as _types

__addon__ = _RhombusAddon(
    name="Tectonic",
    preview_scripts=[_files("rhombus.support.tectonic").joinpath("deepslate.ts")],
    density_functions={
        cls.id: cls
        for name, cls in _types.__dict__.items()
        if isinstance(cls, type)
        and issubclass(cls, _DensityFunction)
        and hasattr(cls, "id")
    },
)
