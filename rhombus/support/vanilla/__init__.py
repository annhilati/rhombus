from . import types
from . import legacy_types

from rhombus.core.environment import ModExtension as _ModExtension
from rhombus.core.models.density_function import DensityFunction as _DensityFunction

__extension__ = _ModExtension(
    namespace="datapack",
    version=(125, 0), # 26.3-snapshot-5
    density_functions=[
        cls
        for name, cls in {**types.__dict__, **legacy_types.__dict__}.items()
        if not name.startswith("_")
        and isinstance(cls, type)
        and issubclass(cls, _DensityFunction)
        and hasattr(cls, "id")
    ]
)
