"""### [ikbLib](https://modrinth.com/mod/ikblib) by ikkyblob

ikbLib is a library mod featuring a family of new voronoi/cellular noise density functions, plus API for seeded density functions.

---
[Wiki](https://github.com/ikkyblob/ikbLib/wiki)
"""

from .functions import *
from . import types

from rhombus.core.environment import ModExtension as _ModExtension
from rhombus.core.models.density_function import DensityFunction as _DensityFunction

__extension__ = _ModExtension(
    namespace="ikblibrary",
    version=(1, 0, 0),
    preview_scripts=[],
    density_functions={
        cls.id: cls
        for name, cls in types.__dict__.items()
        if isinstance(cls, type)
        and issubclass(cls, _DensityFunction)
        and hasattr(cls, "id")
    },
)
