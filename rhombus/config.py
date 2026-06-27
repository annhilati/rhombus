from typing import Iterable, Any, TYPE_CHECKING
from types import ModuleType
from contextvars import ContextVar
from dataclasses import dataclass
import beet, warnings, threading

if TYPE_CHECKING:
    from rhombus.core import DensityFunction

#======// Environment //=========================================================================//

class RhombusEnvironment:

    def __init__(self):

        self.datapack: beet.DataPack | None = None
        self.deserialize_reference_with_content: bool = False
        self.infinitesimal: float = 1e-16
        self.REGISTERED_DENSITY_FUNCTION_TYPES: dict[str, type["DensityFunction"]] = {}
        "Mapping of all defined classes inheriting from `DensityFunction` with their ids as the keys."
        self.caching_function_types: set[type["DensityFunction"]] = set()
        
        self._reg_lock = threading.RLock()
        

_current_env: ContextVar[RhombusEnvironment] = ContextVar("current_env")

class _EnvProxy:
    
    @property
    def _current(self) -> RhombusEnvironment:
        try:
            return _current_env.get()
        except LookupError:
            env = RhombusEnvironment()
            _current_env.set(env)
            return env
        
    def __getattr__(self, name):
        return getattr(self._current, name)
    def __setattr__(self, name, value):
        setattr(self._current, name, value)

if TYPE_CHECKING:
    ctx = RhombusEnvironment()
    env = RhombusEnvironment()
else:
    ctx = _EnvProxy()
    env = _EnvProxy()

@dataclass
class RhombusAddon:

    def run(self) -> None:
        pass


def register(*add: type["DensityFunction"] | ModuleType | Any, rm: Iterable[str | type["DensityFunction"]] = []) -> dict[str, tuple[str, type["DensityFunction"]]]:
    """Registers or removes `DensityFunction` type subclasses from the deserialization register.
    
    Parameters:
        *add (type[DensityFunction] | module | Any): Objects to register density function types from.
            If it is not a `DensityFunction` subclass, its attributes will be searched for
            such. If it is a module, the serach is recursive.
        rm (str | type[DensityFunction]): Density function types to remove from the deserialization register.

    Returns:
        The deserialization register after registration. Maps density function
            type identifiers to tuples of the selected `DensityFunction` classes'
            module paths and type objects.
    """
    registrations = {}
    visited = set()

    def try_register(o: Any):
        from rhombus.core.density_function import DensityFunction
        if id(o) in visited:
            return
        visited.add(id(o))
        
        if isinstance(o, type) and issubclass(o, DensityFunction):
            if hasattr(o, "id") and isinstance(o.id, str):
                registrations[o.id] = o
        else:
            if hasattr(o, "__dict__"):
                for attribute in o.__dict__.values():
                    try_register(attribute)

    from rhombus.core.density_function import DensityFunction
    for o in add:
        if isinstance(o, type) and issubclass(o, DensityFunction):
            if not hasattr(o, "id") or not isinstance(o.id, str):
                raise ValueError(f"Cannot register density function type '{o.__name__}' without class variable 'id' defined")
            
        try_register(o)

    env.REGISTERED_DENSITY_FUNCTION_TYPES |= registrations

    for rem in rm:
        if isinstance(rem, str):
            keys_to_remove = [k for k in env.REGISTERED_DENSITY_FUNCTION_TYPES if k == rem or (":" not in rem and k == f"minecraft:{rem}")]
            for k in keys_to_remove:
                env.REGISTERED_DENSITY_FUNCTION_TYPES.pop(k, None)
        elif isinstance(rem, type):
            keys_to_remove = [k for k, v in env.REGISTERED_DENSITY_FUNCTION_TYPES.items() if v is rem]
            for k in keys_to_remove:
                env.REGISTERED_DENSITY_FUNCTION_TYPES.pop(k, None)

    if add and not registrations:
        warnings.warn("No DensityFunction subclasses were found to register from the given objects", UserWarning)

    return {id: (f"{typ.__module__}.{typ.__qualname__}", typ) for id, typ in sorted(env.REGISTERED_DENSITY_FUNCTION_TYPES.items())}

def warn(message, category, filename, lineno, file=None, line=None):
    print(
        f"\033[38;2;220;150;80mRhombus Warning\n"
        f"╰─×\033[0m {message}\n"
    )

warnings.showwarning = warn
