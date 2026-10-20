---
title: Extensions
icon: lucide/package-plus
---
# Extensions

Extensions are used in Rhombus to facilitate certain workflows.
They are almost always used with Minecraft mods to provide support for them.

## Declaring an Extension

Extensions are declared as a `__extension__` value of type `ModExtension` inside a module's root.

```py
from .functions import *
from .fast_noise_config import FastNoiseConfig, LithostitchedFastNoiseConfig

from importlib.resources import files
from rhombus.core.config import ModExtension
from rhombus.core.density_function import DensityFunction
from . import types

__extension__ = ModExtension(
    name="Lithostitched",
    preview_scripts=[
        files("rhombus.support.lithostitched").joinpath("fastnoise-lite.ts"),
        files("rhombus.support.lithostitched").joinpath("deepslate.ts"),
    ],
    preview_beet_file_extensions={LithostitchedFastNoiseConfig},
    density_functions={
        cls.id: cls
        for name, cls in types.__dict__.items()
        if isinstance(cls, type)
        and issubclass(cls, DensityFunction)
        and hasattr(cls, "id")
    },
)
```

See the available parameters for extensions at the [`ModExtension` page](../reference/rhombus/core/environment/ModExtension/).