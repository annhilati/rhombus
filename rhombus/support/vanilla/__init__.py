from . import types
from . import legacy_types

from rhombus.core.environment import RhombusAddon as _RhombusAddon
from rhombus.core.density_function import DensityFunction as _DensityFunction

__addon__ = _RhombusAddon(
    namespace="datapack",
    version=(118, 0), # 26.3
    density_functions=[
        cls
        for name, cls in {**types.__dict__, **legacy_types.__dict__}.items()
        if not name.startswith("_")
        and isinstance(cls, type)
        and issubclass(cls, _DensityFunction)
        and hasattr(cls, "id")
    ]
)
