"""### [Tectonic](https://modrinth.com/datapack/tectonic) by Apollo

Exposes custom density functions and configuration nodes utilized by the Tectonic world generation mod.
This allows for seamless integration and modification of Tectonic's distinctive terrain features.
"""

from .functions import invert, config_noise, config_constant

__version__ = "3.0.19"

def _register_rhombus_addon() -> None:
    from importlib.resources import files
    
    from rhombus.config import env
    from rhombus.core.density_function import DensityFunction
    
    from . import types

    env.preview_scripts.append(files("rhombus.support.tectonic").joinpath("deepslate.ts"))
    
    env.density_function_type_deserialization_register.update({
        cls.id: cls for name, cls in types.__dict__.items()
        if isinstance(cls, type) and issubclass(cls, DensityFunction) and hasattr(cls, "id")
    })