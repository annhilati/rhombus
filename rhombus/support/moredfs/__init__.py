"""### [More Density Functions](https://modrinth.com/mod/more-density-functions) by Klinbee

Introduces advanced mathematical and utility density function types beyond the vanilla capabilities.
This module significantly expands the flexibility of terrain generation by adding complex operations and samplers.

---
[Wiki](https://github.com/klinbee/More-Density-Functions/wiki)
"""

__version__ = "2.2.1"

from .functions import *
from .sub_parameters import DerivativeComponent, DistanceMetric, ExtraOctaves, RandomSampler

from importlib.resources import files as _files
from rhombus.core.config import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction
from . import types as _types

__addon__ = _RhombusAddon(
    name="MoreDfsAddon",
    preview_scripts=[_files("rhombus.support.moredfs").joinpath("deepslate.ts")],
    density_functions={
        cls.id: cls for name, cls in _types.__dict__.items()
        if isinstance(cls, type) and issubclass(cls, _DensityFunction) and hasattr(cls, "id")
    }
)