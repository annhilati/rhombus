"""### [More Density Functions](https://modrinth.com/mod/more-density-functions) by Klinbee

Introduces advanced mathematical and utility density function types beyond the vanilla capabilities.
This module significantly expands the flexibility of terrain generation by adding complex operations and samplers.

---
[Wiki](https://github.com/klinbee/More-Density-Functions/wiki)
"""

__version__ = "2.2.1"

from .functions import *
from .sub_parameters import DerivativeComponent, DistanceMetric, ExtraOctaves, RandomSampler

def _register_rhombus_addon() -> None:
    from importlib.resources import files
    
    from rhombus.core.config import env
    from rhombus.core.density_function import DensityFunction
    
    from . import types

    env.preview_scripts.append(files("rhombus.support.moredfs").joinpath("deepslate.ts"))
    
    env.density_function_type_deserialization_register.update({
        cls.id: cls for name, cls in types.__dict__.items()
        if isinstance(cls, type) and issubclass(cls, DensityFunction) and hasattr(cls, "id")
    })