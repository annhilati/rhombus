from __future__ import annotations

__all__ = ["RhombusVersion", "DatapackVersion", "VersionTuple", "VersionSpecifier", "RhombusEnvironment", "RhombusAddon", "rho", "get_module_addon_namespace", "FROM_CONTEXT", "datapack_handler"]

from typing import Callable, Any, Optional, Final, overload, TYPE_CHECKING
from types import ModuleType, EllipsisType
from dataclasses import dataclass, field
from functools import total_ordering
from pathlib import Path
import threading
import re
import sys
import functools
import inspect
import copy

import beet

if TYPE_CHECKING:
    from rhombus.core import DensityFunction
    from rhombus.core.utils import BeetFile

from rhombus.core.utils import GlobalBinding, get_Minecraft_datapack_version


# ======// Versioning //==========================================================================//

type DatapackVersion = float | int
type VersionString = str
type VersionTuple = tuple[int | str, ...] | tuple[str, tuple[int | str, ...]]
type VersionSpecifier = DatapackVersion | VersionTuple | VersionString


def get_module_addon_namespace(module_path: str) -> str | None:
    "Recursively searches in a module and its parents for the `__addon__` declaration and returns the addons namespace."
    parts = module_path.split('.')
    while parts:
        current_module_name = '.'.join(parts)
        module = sys.modules.get(current_module_name)
        if module and hasattr(module, "__addon__"):
            return getattr(module, "__addon__").namespace
        parts.pop()
    return None

@total_ordering
class _VersionPart:
    def __init__(self, val: int | str):
        self.val = val
        if isinstance(val, int):
            self.parts = (val,)
        else:
            self.parts = tuple(int(x) if x.isdigit() else x for x in re.split(r'(\d+)', val) if x)

    def __eq__(self, other):
        if not isinstance(other, _VersionPart): return False
        return self.parts == other.parts

    def __lt__(self, other):
        if not isinstance(other, _VersionPart): return NotImplemented
        for p1, p2 in zip(self.parts, other.parts):
            if type(p1) == type(p2):
                if p1 != p2: return p1 < p2
            else:
                return isinstance(p1, str)
        return len(self.parts) < len(other.parts)

@total_ordering
class RhombusVersion:
    """Internal representation of a version for Rhombus, capable of natural sorting and parsing.
    
    This class is primarily used internally to normalize and compare version specifiers.
    
    Supported formats for VersionSpecifier (and what they parse to):
    - Float/Int: `1.20` -> namespace="datapack", version=(1, 20)
                 `118`  -> namespace="datapack", version=(118, 0)
                 `9.0`  -> namespace="datapack", version=(9, 0)
    - String:    `"1.20.4"`   -> namespace="datapack", version=(1, 20, 4)
                 `"1.20-rc1"` -> namespace="datapack", version=(1, 20, "rc1")
    - Tuple:     `(1, 20)`          -> namespace="datapack", version=(1, 20)
                 `(1, 20, "rc1")`   -> namespace="datapack", version=(1, 20, "rc1")
    - Namespaced Tuple:
                 `("my_mod", (1, 20))`       -> namespace="my_mod", version=(1, 20)
                 `("my_mod", "1.20-rc1")`    -> namespace="my_mod", version=(1, 20, "rc1")
    """
    namespace: str
    version: tuple[int | str, ...]

    def __init__(
        self,
        spec: VersionSpecifier | "RhombusVersion",
        default_namespace: str = "datapack",
    ):
        if isinstance(spec, RhombusVersion):
            self.namespace = spec.namespace
            self.version = spec.version
        elif isinstance(spec, (float, int)):
            self.namespace = default_namespace
            parts = str(float(spec)).split(".")
            self.version = tuple(int(p) for p in parts)
        elif isinstance(spec, str):
            self.namespace = default_namespace
            # Extracts words (rc, beta) and numbers, ignoring dots/hyphens
            parts = [int(p) if p.isdigit() else p for p in re.findall(r'[a-zA-Z]+|\d+', spec)]
            self.version = tuple(parts)
        elif isinstance(spec, tuple):
            if len(spec) >= 2 and isinstance(spec[0], str):
                self.namespace = spec[0]
                inner = spec[1]
                if isinstance(inner, tuple):
                    self.version = inner
                elif isinstance(inner, (float, int)):
                    parts = str(float(inner)).split(".")
                    self.version = tuple(int(p) for p in parts)
                elif isinstance(inner, str):
                    parts = [int(p) if p.isdigit() else p for p in re.findall(r'[a-zA-Z]+|\d+', inner)]
                    self.version = tuple(parts)
                else:
                    self.version = (inner,)
            else:
                self.namespace = default_namespace
                self.version = spec
        else:
            raise TypeError(f"Invalid version specifier: {spec}")

    def __hash__(self):
        v = list(self.version)
        while v and v[-1] == 0:
            v.pop()
        return hash((self.namespace, tuple(v)))

    def _get_comparable_parts(self) -> tuple[_VersionPart, ...]:
        return tuple(_VersionPart(p) for p in self.version)

    def __eq__(self, other):
        if not isinstance(other, RhombusVersion):
            try:
                other = RhombusVersion(other)
            except Exception:
                return NotImplemented
        if self.namespace != other.namespace:
            return False
        
        parts1 = list(self._get_comparable_parts())
        parts2 = list(other._get_comparable_parts())
        
        length = max(len(parts1), len(parts2))
        parts1 += [_VersionPart(0)] * (length - len(parts1))
        parts2 += [_VersionPart(0)] * (length - len(parts2))
        
        return parts1 == parts2

    def __lt__(self, other):
        if not isinstance(other, RhombusVersion):
            try:
                other = RhombusVersion(other)
            except Exception:
                return NotImplemented
        if self.namespace != other.namespace:
            return NotImplemented
            
        parts1 = list(self._get_comparable_parts())
        parts2 = list(other._get_comparable_parts())
        
        length = max(len(parts1), len(parts2))
        parts1 += [_VersionPart(0)] * (length - len(parts1))
        parts2 += [_VersionPart(0)] * (length - len(parts2))
        
        return parts1 < parts2

    def __repr__(self) -> str:
        return f"RhombusVersion({self.namespace!r}, {self.version})"


# ======// Environment //=========================================================================//


class VersionsDict(dict[str, VersionSpecifier]):
    def __setitem__(self, key: str, value: VersionSpecifier):
        rv = RhombusVersion(value, default_namespace=key)
        super().__setitem__(key, rv.version)
        
    def update(self, other=(), **kwargs):
        if hasattr(other, "keys"):
            for k in other.keys():
                self[k] = other[k]
        else:
            for k, v in other:
                self[k] = v
        for k, v in kwargs.items():
            self[k] = v


class RhombusEnvironment:

    def __init__(self):

        # Context
        self.datapack: beet.DataPack | None = None

        # Configuration
        self.versions: VersionsDict = VersionsDict()
        self.deserialize_references_inline: bool = False
        """When `deserialize_references_inline` is `True`, references to density
        functions in other files will be inlined, such that they are no longer
        different files but one combined abstract syntax tree instead.
        """

        # Registries
        self.density_function_type_deserialization_register: dict[str, type["DensityFunction"]] = {}
        "Mapping of all `DensityFunction` subclasses that are used for deserialization, with their ids as the keys."
        self.caching_function_types: set[type["DensityFunction"]] = set() # TODO: remove?
        "Set of `DensityFunction` subclasses that apply structuring logic for enabling caching"

        # Preview
        self.preview_beet_file_extensions: set[type["BeetFile"]] = set()
        "Set of `BeetFile` representing datapack files to include when previewing a datapack."  # This was introduces for the CLI, so addons can be stated
        self.preview_file_icons: dict[str, str] = {}
        "Mapping of svg file icons and corresponding Regex expressions that are tested on the registry ids (without namespace)"
        self.preview_scripts: list[str | Path] = []
        """Paths of JavaScript or TypeScript files in this attribute will be loaded by
        Rhombus Preview and patched into Deepslate.

        This allows plugins to add functionality to the webapp, like registering a custom
        decoding register or providing visualization patches for the preview.
        """

        # State
        self._addons: set["RhombusAddon"] = set()
        self._id_counter: int = 0
        self._reg_lock = threading.RLock()


    @property
    def datapack_version(self) -> float:
        val = self.versions.get("datapack", (118, 0))
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, tuple) and len(val) >= 1:
            if len(val) == 1:
                return float(val[0])
            else:
                # To handle cases like (41, 0) or (1, 18)
                if val[0] == 1:
                    return float(f"1.{val[1]}")
                return float(val[0] + (val[1] * 0.1 if val[1] < 10 else val[1] * 0.01))
        return 0.0

    @datapack_version.setter
    def datapack_version(self, value: DatapackVersion | tuple[int | str] | tuple[int | str, int | str]):
        if value is None:
            raise ValueError("datapack_version cannot be None.")
        if not isinstance(value, (int, float, tuple)):
            raise TypeError("datapack_version must be a float, int, or a 1-/2-tuple.")
        if isinstance(value, tuple) and len(value) not in (1, 2):
            raise ValueError("datapack_version tuple must have 1 or 2 elements.")
        self.versions["datapack"] = value

    # TODO: Remove mod versioning here again, because we have them in load_addons?
    @overload
    def set_version(self, *, datapack: DatapackVersion, **mods: VersionTuple | VersionString) -> None: ...
    @overload
    def set_version(self, *, minecraft: str, **mods: VersionTuple | VersionString) -> None: ...
    @overload
    def set_version(self, **mods: VersionTuple | VersionString) -> None: ...

    def set_version(self, **kwargs) -> None:
        """Sets the datapack version and/or addon versions.
        If a Minecraft version string (e.g. '1.21.4') is provided, it is resolved to a datapack version using Misode's data.
        """
        if kwargs.get("datapack") is not None and kwargs.get("minecraft") is not None:
            raise ValueError("Cannot accept both 'datapack' and 'minecraft' arguments")

        if (minecraft_arg := kwargs.pop("minecraft", None)) is not None:
            if isinstance(minecraft_arg, (float, int)):
                raise TypeError("Please provide Minecraft game versions only as strings")
            if isinstance(minecraft_arg, str) and minecraft_arg.count('.') == 1:
                try:
                    self.datapack_version = get_Minecraft_datapack_version(minecraft_arg, use_cache=True)
                except ValueError:
                    # Try appending '0'
                    self.datapack_version = get_Minecraft_datapack_version(minecraft_arg + "0", use_cache=True)
            else:
                self.datapack_version = get_Minecraft_datapack_version(minecraft_arg, use_cache=True)

        elif (datapack_arg := kwargs.pop("datapack", None)) is not None:
            self.datapack_version = datapack_arg
            
        for mod, ver in kwargs.items():
            self.versions[mod] = ver

    def load_addons(self, addons: dict[ModuleType | "RhombusAddon", VersionString | EllipsisType]) -> None:
        """Loads addons for Rhombus and calls their individual registration procedures.

        Addon registration typically includes adding custom density function types to the
        decoding register or providing visualization patches for the preview.
        """
        for addon_target, version in addons.items():
            if isinstance(addon_target, ModuleType):
                if not hasattr(addon_target, "__addon__"):
                    raise ValueError(
                        f"Module {addon_target.__name__} does not contain an '__addon__' attribute."
                    )
                addon_obj = addon_target.__addon__
            elif isinstance(addon_target, RhombusAddon):
                addon_obj = addon_target
            else:
                raise ValueError(
                    f"Addon target {addon_target!r} is neither a module nor a RhombusAddon instance."
                )

            if not hasattr(addon_obj, "apply_to_rhombus_env"):
                raise ValueError(
                    f"Object {addon_obj!r} is not a valid Rhombus Addon. "
                    "It is missing an 'apply_to_rhombus_env' method"
                )

            addon_obj.apply_to_rhombus_env(self)
            self._addons.add(addon_obj)
            
            # Write the specified version to the environment's active versions dict
            self.versions[addon_obj.namespace] = version

    # TODO: Does this implementation make sense?
    def _check_version(self, spec: VersionSpecifier | EllipsisType) -> bool | None:
        """Prüft, ob die Version der Umgebung den Anforderungen entspricht.
        Gibt None zurück, wenn die Version der Umgebung unbekannt ist."""
        if spec is ...:
            return False
        req = RhombusVersion(spec)
        
        current_v = self.versions.get(req.namespace)
        if current_v is None:
            return None
        return RhombusVersion((req.namespace, current_v)) >= req



# ======// Addon //===============================================================================//

@dataclass
class RhombusAddon:
    """The **`RhombusAddon`** class declares an addon for the Rhombus runtime
    environment.

    Add-ons are used to facilitate certain workflows.
    They are almost always used with Minecraft mods to provide support for them.

    ## Declaring an Addon

    Addons are declared as a `__addon__` value inside a module's root.

    **Example:**
    ```
    from .functions import *
    from .fast_noise_config import FastNoiseConfig, LithostitchedFastNoiseConfig

    from importlib.resources import files
    from rhombus.core.config import RhombusAddon
    from rhombus.core.density_function import DensityFunction
    from . import types

    __addon__ = RhombusAddon(
        namespace="Lithostitched",
        default_version=(1, 20),
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
        }
    )
    ```

    Parameters:
        namespace (str): Identifier for the addon
        default_version (VersionLike | None): The default version to set in the environment when the addon is loaded.
        density_functions (dict[str, DensityFunction]): Mapping of additional density function types
            (their identifiers) as the keys. This is mainly used for deserializing density function from JSON dictionaries.
        caching_functions (set[DensityFunction]): Density function types to which
            a specific treatment is applied to ensure efficient caching.
        preview_scripts (list[str | Path]): Paths of JavaScript or TypeScript files that will be provided
            by the Rhombus Preview service, such that they are available in the previewing frontend.
            It is recommended to provide these paths with the `files().joinpath()` method from `importlib.resources`.
        preview_beet_file_extensions (set[BeetFile]): Beet file classes for datapack file types to include in the
            Rhombus Preview. 
        on_apply (Optional[Callable[[RhombusEnvironment], Any]]): Custom function that is called, when the addon is loaded.
    """

    namespace: str
    default_version: VersionSpecifier | None = None
    density_functions: dict[str, type["DensityFunction"]] | list[type["DensityFunction"]] = field(default_factory=dict)
    caching_functions: set[type["DensityFunction"]] = field(default_factory=set)
    preview_scripts: list[str | Path] = field(default_factory=list)
    preview_beet_file_extensions: set[type["BeetFile"]] = field(default_factory=set)
    on_apply: Optional[Callable[["RhombusEnvironment"], Any]] = None

    def __hash__(self):
        return hash(self.namespace)

    def __eq__(self, other):
        return isinstance(other, RhombusAddon) and self.namespace == other.namespace

    def apply_to_rhombus_env(self, env: "RhombusEnvironment") -> None:
        if self.on_apply:
            self.on_apply(env)
            
        if self.default_version is not None and self.namespace not in env.versions:
            env.versions[self.namespace] = self.default_version
        if isinstance(self.density_functions, dict):
            env.density_function_type_deserialization_register.update(self.density_functions)
        else:
            def _extract_all_known_ids(cls: type) -> list[str]:
                if not hasattr(cls, "id"):
                    return []
                ids = [getattr(cls, "id")]
                legacy = getattr(cls, "__rhombus_legacy_values__", {})
                if "id" in legacy:
                    ids.extend(legacy["id"].values())
                return ids

            for cls in self.density_functions:
                for fid in _extract_all_known_ids(cls):
                    if fid:
                        env.density_function_type_deserialization_register[fid] = cls
                        
        env.caching_function_types.update(self.caching_functions)
        env.preview_scripts.extend(self.preview_scripts)
        env.preview_beet_file_extensions.update(self.preview_beet_file_extensions)


# TODO: rhombus.core should not include runtime relevant symbols.
# Thus 'env' should be moved somewhere else in the future.
rho: RhombusEnvironment = GlobalBinding(RhombusEnvironment)
"""The default global Rhombus environment.

For more information on how to use environments see
[`RhombusEnvironment`](https://annhilati.github.io/rhombus/reference/rhombus/core/environment/RhombusEnvironment/).
"""

FROM_CONTEXT: Final = object()
"Typing sentinel to denote that a value will be adopted from the environment."

def datapack_handler[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that handles the 'dp' parameter for datapack contexts.
    If 'dp' is FROM_CONTEXT, it injects the current env.datapack.
    If 'dp' is provided explicitly, it temporarily overrides env.datapack 
    for the duration of the function call, restoring it afterwards.
    """
    sig = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        if "dp" in bound.arguments:
            value = bound.arguments["dp"]

            if value is FROM_CONTEXT:
                bound.arguments["dp"] = rho.datapack
                return func(*bound.args, **bound.kwargs)  # type: ignore
            elif value is not rho.datapack:
                # Temporarily override the environment with the new datapack
                current_env_obj: RhombusEnvironment = rho._get_instance()
                new_env = copy.copy(current_env_obj)
                new_env.datapack = value

                token = rho._ctxvar.set(new_env)
                try:
                    return func(*bound.args, **bound.kwargs)  # type: ignore
                finally:
                    rho._ctxvar.reset(token)
            else:
                # Value is already the current environment datapack
                return func(*bound.args, **bound.kwargs)  # type: ignore
        else:
            return func(*bound.args, **bound.kwargs)  # type: ignore

    wrapper.__signature__ = sig  # type: ignore
    return wrapper
