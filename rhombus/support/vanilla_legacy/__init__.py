from rhombus.core.environment import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction

from . import types as _types
from .types import *

__version__ = "26.3"

__addon__ = _RhombusAddon(
    name="VanillaLegacy",
    density_functions={
        cls.id: cls
        for name, cls in _types.__dict__.items()
        if name in _types.__all__
        and isinstance(cls, type)
        and issubclass(cls, _DensityFunction)
        and hasattr(cls, "id")
    },
)
