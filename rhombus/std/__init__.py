"""
# The Rhombus standard library
This module contains all the symbols needed to develop vanilla terrain
generation for datapacks, as well as some tools that are generally well-
suited for this purpose.

Typically, when developing terrain generation, you will want to import
everything from this module. Note that some builtin symbols from Python
might be overwritten. To get them back, you can import from `builtins`.

```
from rhombus import *
from builtins import abs as python_abs
```
"""

__version__ = "26.2"

from rhombus.std.noise import *
from rhombus.std.macros import *
from rhombus.std.density import *
from rhombus.std.functions import *
from rhombus.std import functions as f
from rhombus.std import types as t

def _register_rhombus_addon() -> None:
    from importlib.resources import files
    
    from rhombus.config import env
    from rhombus.core.density_function import DensityFunction
    
    from . import types
   
    env.density_function_type_deserialization_register.update({
        cls.id: cls for name, cls in types.__dict__.items()
        if name in types.__all__ and isinstance(cls, type) and issubclass(cls, DensityFunction) and hasattr(cls, "id")
    })
    env.caching_function_types.update({t.cache_2d, t.flat_cache, t.cache_all_in_cell, t.cache_once})