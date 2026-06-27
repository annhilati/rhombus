from typing import Protocol, TYPE_CHECKING
from pathlib import Path
from contextvars import ContextVar
import beet, warnings, threading

if TYPE_CHECKING:
    from rhombus.core import DensityFunction


class RhombusAddon(Protocol):
    def _register_rhombus_addon() -> None:
        pass


#======// Environment //=========================================================================//

class RhombusEnvironment:

    def __init__(self):

        # Context
        self.datapack: beet.DataPack | None = None

        # Configuration
        self.deserialize_references_directly: bool = False
        self.infinitesimal: float = 1e-16

        # Registries
        self.REGISTERED_DENSITY_FUNCTION_TYPES: dict[str, type["DensityFunction"]] = {}
        "Mapping of all defined classes inheriting from `DensityFunction` with their ids as the keys."
        self.caching_function_types: set[type["DensityFunction"]] = set()
        "Set of `DensityFunction` subclasses that apply structuring logic for enabling caching"
        self.preview_file_icons: dict[str, str] = {}
        "Mapping of svg file icons and corresponding Regex expressions that are tested on the registry ids (without namespace)"
        self.preview_scripts: list[str | Path] = []
        """Paths of JavaScript files in this attribute will be loaded by
        Rhombus Preview and patched into Deepslate.

        This could look like this:
        ```
        env.preview_scripts.append(files("rhombus.support.lithostitched").joinpath("sqrt.js"))
        ```
        """
        
        # Just because why not, we document what addons were loaded in which order
        self._addons: list[RhombusAddon] = []

        self._reg_lock = threading.RLock()


    @staticmethod
    def load(*addons: RhombusAddon) -> None:
        """Loads addons for Rhombus and calls their individual registration procedures.
        
        Addon registration typically includes adding custom density function types to the
        decoding register or providing visualization patches for the preview.

        `RhombusAddon` is a protocoll requiring the `_register_rhombus_addon` method.
        This can be a module or a class and principially also any other object.
        """
        for addon in addons:
            if not hasattr(addon, "_register_rhombus_addon"):
                raise ValueError(
                    f"Object {addon!r} is not a valid Rhombus Addon. "
                    "It is missing a '_register_rhombus_addon' method"
                )
            addon._register_rhombus_addon()
            env._addons.append(addon)
        

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
    "Default Rhombus environment"
    env = RhombusEnvironment()
    "Default Rhombus environment"
else:
    ctx = _EnvProxy()
    env = _EnvProxy()


def warn(message, category, filename, lineno, file=None, line=None):
    print(
        f"\033[38;2;220;150;80mRhombus Warning\n"
        f"╰─×\033[0m {message}\n"
    )

warnings.showwarning = warn
