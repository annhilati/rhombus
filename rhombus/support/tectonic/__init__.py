"""### [Tectonic](https://modrinth.com/datapack/tectonic) by Apollo

Exposes custom density functions and configuration nodes utilized by the Tectonic world generation mod.
This allows for seamless integration and modification of Tectonic's distinctive terrain features.
"""

from .functions import invert, config_noise, config_constant
from . import types

from rhombus.core.environment import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction

__addon__ = _RhombusAddon(
    namespace="tectonic",
    version=(3, 0, 19),
    preview_scripts=[_RhombusAddon.resource("rhombus.support.tectonic", "deepslate.ts")],
    density_functions={
        cls.id: cls
        for name, cls in types.__dict__.items()
        if isinstance(cls, type)
        and issubclass(cls, _DensityFunction)
        and hasattr(cls, "id")
    },
)
