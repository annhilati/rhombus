---
title: Addons
icon: lucide/package-plus
---
# Addons

Add-ons are used in Rhombus to facilitate certain workflows.
They are almost always used with Minecraft mods to provide support for them.

## Declaring an Addon

Addons are declared as a `__addon__` value of type `RhombusAddon` inside a module's root.

```py
from .functions import *
from .fast_noise_config import FastNoiseConfig, LithostitchedFastNoiseConfig

from importlib.resources import files
from rhombus.core.config import RhombusAddon
from rhombus.core.density_function import DensityFunction
from . import types

__addon__ = RhombusAddon(
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

See the available parameters for addons at the [`RhombusAddon` page](https://annhilati.github.io/rhombus/reference/rhombus/core/config/RhombusAddon/#rhombusaddon).