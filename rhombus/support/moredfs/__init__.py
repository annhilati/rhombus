"""### [More Density Functions](https://modrinth.com/mod/more-density-functions) by Klinbee

Introduces advanced mathematical and utility density function types beyond the vanilla capabilities.
This module significantly expands the flexibility of terrain generation by adding complex operations and samplers.

---
[Wiki](https://github.com/klinbee/More-Density-Functions/wiki)
[Modrinth](https://modrinth.com/mod/more-density-functions)"""

__version__ = "2.2.1"

from .functions import *
from .sub_parameters import DerivativeComponent, DistanceMetric, ExtraOctaves, RandomSampler