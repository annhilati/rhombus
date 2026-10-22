from __future__ import annotations

__all__ = ["DatapackVersion", "VersionTuple", "RhombusEnvironment", "ModExtension", "get_module_extension_namespace", "parse_version_specifier"]

from typing import Callable, Any, Optional, Protocol, overload, TYPE_CHECKING
from types import ModuleType, EllipsisType
from pathlib import Path
from dataclasses import dataclass, field
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
type NamespacedVersion = tuple[str, VersionTuple]


def parse_version_specifier(spec: DatapackVersion | VersionString | VersionTuple, interpret_as_game_version_convert_to_datapack_version: bool = False) -> VersionTuple:
    
    def parse_VersionString(spec: VersionString) -> VersionTuple:
        return tuple(int(p) for p in spec.split("."))
    
    if isinstance(spec, (int, float)):
        if interpret_as_game_version_convert_to_datapack_version:
            try:
                return parse_version_specifier(get_Minecraft_datapack_version(str(float(spec))))
            except ValueError:
                pass
        parts = parse_VersionString(str(float(spec)))
        if isinstance(spec, float) and len(parts) >= 2 and parts[0] == 1 and parts[1] < 10:
            parts = (parts[0], parts[1] * 10, *parts[2:])
        if len(parts) == 1:
            parts = (*parts, 0)
        return parts
    
    elif isinstance(spec, str):
        if interpret_as_game_version_convert_to_datapack_version:
            try:
                return parse_version_specifier(get_Minecraft_datapack_version(spec))
            except ValueError:
                pass
        parts = parse_VersionString(spec)
        if len(parts) == 1:
            parts = (*parts, 0)
        return parts
    
    elif isinstance(spec, tuple):
        if not all(isinstance(part, int) for part in spec):
            raise ValueError(f"Some parts of {spec} are not of type int or float")
        if interpret_as_game_version_convert_to_datapack_version:
            try:
                return parse_version_specifier(get_Minecraft_datapack_version(".".join(str(p) for p in spec)))
            except ValueError:
                pass
        if len(spec) == 1:
            return (*spec, 0)
        return spec
        
    raise TypeError(f"Cannot parse object of type {type(spec)} to version")


def get_module_extension_namespace(module_path: str) -> str | None:
    """Recursively searches in a module and its parents for the `__extension__` declaration and returns the extensions namespace."""
    parts = module_path.split('.')
    while parts:
        current_module_name = '.'.join(parts)
        if (module := sys.modules.get(current_module_name)) and hasattr(module, "__extension__"):
            return module.__extension__.namespace
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
        """When `True`, references to density
        functions in other files will be inlined, such that they are no longer
        different files but one combined abstract syntax tree instead.
        """
        self.fetch_reference_definition_from_context: bool = False
        """When `True`, references will try to fetch their definitions from the datapack context on instantiation.
        """

        self.human_readable_names: bool = False
        """When `True`, automatically generated datapack
        files will receive a human readable codename (e.g., "agile_warden_1234")
        instead of a UUID.
        """

        # Registries
        self.density_function_type_deserialization_register: dict[str, type["DensityFunction"]] = {}
        "Mapping of all `DensityFunction` subclasses that are used for deserialization, with their ids as the keys."

        # Preview
        self.preview_beet_file_extensions: set[type["BeetFile"]] = set()
        "Set of `BeetFile` representing datapack files to include when previewing a datapack."  # This was introduces for the CLI, so extensions can be stated
        self.preview_file_icons: dict[str, str] = {}
        "Mapping of svg file icons and corresponding Regex expressions that are tested on the registry ids (without namespace)"
        self.preview_scripts: list[str | Path] = []
        """Paths of JavaScript or TypeScript files in this attribute will be loaded by
        Rhombus Preview and patched into Deepslate.

        This allows plugins to add functionality to the webapp, like registering a custom
        decoding register or providing visualization patches for the preview.
        """

        # State
        self._extensions: set["ModExtension"] = set()
        self._id_counter: int = 0
        self._reg_lock = threading.RLock()


    @property
    def datapack_version(self) -> DatapackVersion:
        """The current datapack version."""
        val = self.versions.get("datapack", (118, 0))
        return float(".".join(str(part) for part in val))

    @datapack_version.setter
    def datapack_version(self, value: DatapackVersion):
        if value is None:
            raise ValueError("datapack_version cannot be None.")
        if not isinstance(value, (int, float)):
            raise TypeError("datapack_version must be a float, int, str, or a tuple.")
        self.versions["datapack"] = parse_version_specifier(value)

    @overload
    def set_version(self, *, datapack: DatapackVersion) -> None: ...
    @overload
    def set_version(self, *, minecraft: VersionString) -> None: ...

    def set_version(self, *args, **kwargs) -> None:
        """Sets the datapack or Minecraft game version.
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

    def require(self, extensions: dict[ModExtensionModule | "ModExtension" | str, VersionString | EllipsisType]) -> None:
        """Loads extensions for Rhombus and calls their individual registration procedures.

        Extension registration typically includes adding custom density function types to the
        decoding register or providing visualization patches for the preview.
        """
        for extension_target, version in extensions.items():
            
            extension_obj: ModExtension | None = None
            extension_ns: str | None
            extension_version: VersionTuple | None
            
            if isinstance(extension_target, ModuleType):
                if not hasattr(extension_target, "__extension__"):
                    raise ValueError(
                        f"Module {extension_target.__name__} does not contain an '__extension__' attribute."
                    )
                self.require({extension_target.__extension__: version})
                continue
                
            elif isinstance(extension_target, str):
                extension_ns = extension_target
                if version is ...:
                    if (known_extension := next(extension for extension in self._extensions if extension.namespace == extension_ns)) and known_extension.version is not None:
                        extension_version = parse_version_specifier(known_extension.version)
                    else:
                        raise ValueError(f"Cannot use default version for extension '{extension_ns}'. No ModExtension was provided")
                else:
                    extension_version = parse_version_specifier(version)
                
            elif isinstance(extension_target, ModExtension):
                extension_obj = extension_target
                extension_ns = extension_obj.namespace
                extension_version = parse_version_specifier(extension_obj.version) if extension_obj.version is not None else None
                
            else:
                raise ValueError(
                    f"Extension target {extension_target!r} is neither a module nor a ModExtension instance."
                )

            if extension_obj is not None:
                extension_obj.apply(self)
                self._extensions.add(extension_obj)

            self.versions[extension_ns] = extension_version


    def _check_version(
        self,
        version: DatapackVersion | VersionString | VersionTuple | EllipsisType,
        namespace: str = "datapack",
    ) -> bool | None:
        """Prüft, ob die Version der Umgebung den Anforderungen entspricht.
        Gibt None zurück, wenn die Version der Umgebung unbekannt ist."""
        if version is ...:
            return False
            
        if isinstance(version, tuple) and all(isinstance(part, int) for part in version):
            req_tuple = version
        else:
            req_tuple = parse_version_specifier(
                version,
                interpret_as_game_version_convert_to_datapack_version=(namespace == "datapack"),
            )
        
        current_v = self.versions.get(namespace)
        if current_v is None:
            return None
            
        # Pad with 0 to match length
        length = max(len(current_v), len(req_tuple))
        current_padded = list(current_v) + [0] * (length - len(current_v))
        req_padded = list(req_tuple) + [0] * (length - len(req_tuple))
        
        return tuple(current_padded) >= tuple(req_padded)



# ======// Extension //===============================================================================//

class ModExtensionModule(Protocol):
    __extension__: ModExtension


@dataclass
class ModExtension:
    """The **`ModExtension`** class declares an extension for the Rhombus runtime
    environment.

    Extensions are used to facilitate certain workflows.
    They are almost always used with Minecraft mods to provide support for them.

    ## Declaring an Extension

    Extensions are declared as a `__extension__` value inside a module's root.

    **Example:**
    ```
    from .functions import *
    from .fast_noise_config import FastNoiseConfig, LithostitchedFastNoiseConfig

    from rhombus.core.config import ModExtension
    from rhombus.core.density_function import DensityFunction
    from . import types

    __extension__ = ModExtension(
        namespace="lithostitched",
        version=(1, 20),
        preview_scripts=[
            ModExtension.resource("rhombus.support.lithostitched", "fastnoise-lite.ts"),
            ModExtension.resource("rhombus.support.lithostitched", "deepslate.ts"),
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
        namespace (str): Identifier for the extension
        version (DatapackVersion | VersionString | VersionTuple | None): The default version to set in the environment when the extension is loaded.
        density_functions (dict[str, DensityFunction]): Mapping of additional density function types
            (their identifiers) as the keys. This is mainly used for deserializing density function from JSON dictionaries.
        preview_scripts (list[str | Path]): Paths of JavaScript or TypeScript files that will be provided
            by the Rhombus Preview service, such that they are available in the previewing frontend.
            It is recommended to provide these paths with the `ModExtension.resource()` method.
        preview_beet_file_extensions (set[BeetFile]): Beet file classes for datapack file types to include in the
            Rhombus Preview. 
        on_apply (Optional[Callable[[RhombusEnvironment], Any]]): Custom function that is called, when the extension is loaded.
    """

    namespace: str
    version: VersionTuple | None = None
    density_functions: dict[str, type["DensityFunction"]] | list[type["DensityFunction"]] = field(default_factory=dict)
    preview_scripts: list[str | Path] = field(default_factory=list)
    preview_beet_file_extensions: set[type["BeetFile"]] = field(default_factory=set)
    on_apply: Optional[Callable[["RhombusEnvironment"], Any]] = None

    def __hash__(self):
        return hash(self.namespace)

    def __eq__(self, other):
        return isinstance(other, ModExtension) and self.namespace == other.namespace

    def apply(self, env: "RhombusEnvironment") -> None:
        if self.on_apply:
            self.on_apply(env)
            
        if self.version is not None and self.namespace not in env.versions:
            env.versions[self.namespace] = self.version
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