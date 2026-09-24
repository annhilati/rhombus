from __future__ import annotations

__all__ = ["DatapackVersion", "VersionTuple", "RhombusEnvironment", "RhombusAddon", "get_module_addon_namespace"]

from typing import Callable, Any, Optional, overload, TYPE_CHECKING
from types import ModuleType, EllipsisType
from dataclasses import dataclass, field
from pathlib import Path
from importlib.resources import files
import threading
import sys

import beet

from rhombus.core.utils import get_Minecraft_datapack_version

if TYPE_CHECKING:
    from rhombus.core import DensityFunction, BeetFile

# ======// Versioning //==========================================================================//


type DatapackVersion = float | int
type VersionString = str
type VersionTuple = tuple[int, ...]


def parseVersionString(spec: str) -> VersionTuple:
    return tuple(int(p) for p in spec.split("."))

def _parse_version_specifier(spec: DatapackVersion | VersionString | VersionTuple | tuple[str, DatapackVersion | VersionString | VersionTuple], default_namespace: str = "datapack") -> tuple[str, VersionTuple]:
    def pad_and_fix_float(parts: tuple[int, ...], from_float: bool = False) -> VersionTuple:
        # Fix float truncation: 1.20 in Python becomes 1.2, which splits to (1, 2).
        if from_float and len(parts) >= 2 and parts[0] == 1 and parts[1] < 10:
            parts = (parts[0], parts[1] * 10, *parts[2:])
        # Pad to at least 2 elements
        if len(parts) == 1:
            parts = (*parts, 0)
        return parts

    if isinstance(spec, (int, float)):
        return default_namespace, pad_and_fix_float(parseVersionString(str(float(spec))), from_float=True)
    if isinstance(spec, str):
        return default_namespace, pad_and_fix_float(parseVersionString(spec), from_float=False)
    if isinstance(spec, tuple):
        if len(spec) >= 2 and isinstance(spec[0], str):
            ns = spec[0]
            inner = spec[1]
            if isinstance(inner, str):
                return ns, pad_and_fix_float(parseVersionString(inner), from_float=False)
            if isinstance(inner, (int, float)):
                return ns, pad_and_fix_float(parseVersionString(str(float(inner))), from_float=True)
            if isinstance(inner, tuple):
                return ns, pad_and_fix_float(inner, from_float=False) # type: ignore
        else:
            return default_namespace, pad_and_fix_float(spec, from_float=False) # type: ignore
    raise TypeError(f"Invalid version specifier: {spec}")

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


# ======// Environment //=========================================================================//


class RhombusEnvironment:

    def __init__(self):

        # Context
        self.datapack: beet.DataPack | None = None

        # Configuration
        self.versions: dict[str, VersionTuple] = {}
        self.deserialize_references_inline: bool = False
        """When `deserialize_references_inline` is `True`, references to density
        functions in other files will be inlined, such that they are no longer
        different files but one combined abstract syntax tree instead.
        """

        self.human_readable_names: bool = False
        """When `human_readable_names` is `True`, automatically generated datapack
        files will receive a human readable codename (e.g., "agile_warden_1234")
        instead of a UUID hash.
        """

        # Registries
        self.density_function_type_deserialization_register: dict[str, type["DensityFunction"]] = {}
        "Mapping of all `DensityFunction` subclasses that are used for deserialization, with their ids as the keys."

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
    def datapack_version(self, value: DatapackVersion | tuple[int, ...] | VersionString):
        if value is None:
            raise ValueError("datapack_version cannot be None.")
        if not isinstance(value, (int, float, tuple, str)):
            raise TypeError("datapack_version must be a float, int, str, or a tuple.")
        _, parsed = _parse_version_specifier(value, default_namespace="datapack")
        self.versions["datapack"] = parsed

    @overload
    def set_version(self, *, datapack: DatapackVersion) -> None: ...
    @overload
    def set_version(self, *, minecraft: VersionString) -> None: ...

    def set_version(self, *args, **kwargs) -> None:
        """Sets the datapack version and/or addon versions.
        If a Minecraft version string (e.g. '1.21.4') is provided, it is resolved to a datapack version using Misode's data.
        """
        if args:
            raise TypeError(
                f"set_version() only accepts keyword arguments. Please specify the target, "
                f"e.g., rho.set_version(datapack={args[0]!r})."
            )
            
        datapack_arg = kwargs.pop("datapack", None)
        minecraft_arg = kwargs.pop("minecraft", None)

        if datapack_arg is not None and minecraft_arg is not None:
            raise ValueError("set_version() cannot accept both 'datapack' and 'minecraft' arguments.")

        if minecraft_arg is not None:
            # Fallback for floats that were truncated (e.g. 1.2 -> 1.20)
            if isinstance(minecraft_arg, float):
                minecraft_arg = str(minecraft_arg)
            if isinstance(minecraft_arg, str) and minecraft_arg.count('.') == 1:
                try:
                    self.datapack_version = get_Minecraft_datapack_version(minecraft_arg, use_cache=True)
                except ValueError:
                    # Try appending '0'
                    self.datapack_version = get_Minecraft_datapack_version(minecraft_arg + "0", use_cache=True)
            else:
                self.datapack_version = get_Minecraft_datapack_version(minecraft_arg, use_cache=True)
        elif datapack_arg is not None:
            self.datapack_version = datapack_arg

    def require(self, addons: dict[ModuleType | "RhombusAddon", VersionString | EllipsisType]) -> None:
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

            if not hasattr(addon_obj, "apply"):
                raise ValueError(
                    f"Object {addon_obj!r} is not a valid Rhombus Addon. "
                    "It is missing an 'apply' method"
                )

            addon_obj.apply(self)
            self._addons.add(addon_obj)
            
            # Write the specified version to the environment's active versions dict
            ver = version if version is not ... else addon_obj.version
            if ver is not None:
                _, parsed = _parse_version_specifier(ver, default_namespace=addon_obj.namespace)
                self.versions[addon_obj.namespace] = parsed

    def _check_version(self, spec: DatapackVersion | VersionString | VersionTuple | tuple[str, DatapackVersion | VersionString | VersionTuple] | EllipsisType) -> bool | None:
        """Prüft, ob die Version der Umgebung den Anforderungen entspricht.
        Gibt None zurück, wenn die Version der Umgebung unbekannt ist."""
        if spec is ...:
            return False
            
        ns, req_tuple = _parse_version_specifier(spec)
        
        current_v = self.versions.get(ns)
        if current_v is None:
            return None
            
        # Pad with 0 to match length
        length = max(len(current_v), len(req_tuple))
        current_padded = list(current_v) + [0] * (length - len(current_v))
        req_padded = list(req_tuple) + [0] * (length - len(req_tuple))
        
        return tuple(current_padded) >= tuple(req_padded)



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

    from rhombus.core.config import RhombusAddon
    from rhombus.core.density_function import DensityFunction
    from . import types

    __addon__ = RhombusAddon(
        namespace="lithostitched",
        version=(1, 20),
        preview_scripts=[
            RhombusAddon.resource("rhombus.support.lithostitched", "fastnoise-lite.ts"),
            RhombusAddon.resource("rhombus.support.lithostitched", "deepslate.ts"),
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
        version (DatapackVersion | VersionString | VersionTuple | None): The default version to set in the environment when the addon is loaded.
        density_functions (dict[str, DensityFunction]): Mapping of additional density function types
            (their identifiers) as the keys. This is mainly used for deserializing density function from JSON dictionaries.
        preview_scripts (list[str | Path]): Paths of JavaScript or TypeScript files that will be provided
            by the Rhombus Preview service, such that they are available in the previewing frontend.
            It is recommended to provide these paths with the `files().joinpath()` method from `importlib.resources`.
        preview_beet_file_extensions (set[BeetFile]): Beet file classes for datapack file types to include in the
            Rhombus Preview. 
        on_apply (Optional[Callable[[RhombusEnvironment], Any]]): Custom function that is called, when the addon is loaded.
    """

    namespace: str
    version: DatapackVersion | VersionString | VersionTuple | None = None
    density_functions: dict[str, type["DensityFunction"]] | list[type["DensityFunction"]] = field(default_factory=dict)
    preview_scripts: list[str | Path] = field(default_factory=list)
    preview_beet_file_extensions: set[type["BeetFile"]] = field(default_factory=set)
    on_apply: Optional[Callable[["RhombusEnvironment"], Any]] = None

    def __hash__(self):
        return hash(self.namespace)

    def __eq__(self, other):
        return isinstance(other, RhombusAddon) and self.namespace == other.namespace

    def apply(self, env: "RhombusEnvironment") -> None:
        if self.on_apply:
            self.on_apply(env)
            
        if self.version is not None and self.namespace not in env.versions:
            _, parsed = _parse_version_specifier(self.version, default_namespace=self.namespace)
            env.versions[self.namespace] = parsed
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
                        
        env.preview_scripts.extend(self.preview_scripts)
        env.preview_beet_file_extensions.update(self.preview_beet_file_extensions)


    @staticmethod
    def resource(module_path: str, file_name: str):
        """Returns the path for a file located in a directory that is also a Python module.
        
        This is just a helper implementing `importlib.resources.files(module_path).joinpath(file_name)`.
        """
        return files(module_path).joinpath(file_name)