"""Provides backward compatibility for Minecraft world generation features that have been altered or removed.

This module restores legacy density functions and noise types to maintain compatibility with older world designs.
When importing from this module, ensure it is done after importing standard symbols to avoid conflicts.
"""

from .functions import *
from . import types

def _register_rhombus_addon() -> None:  
    from rhombus.core.config import env
    from rhombus.core.density_function import DensityFunction
    
    from . import types
    
    env.density_function_type_deserialization_register.update({
        cls.id: cls for name, cls in types.__dict__.items()
        if isinstance(cls, type) and issubclass(cls, DensityFunction) and hasattr(cls, "id")
    })