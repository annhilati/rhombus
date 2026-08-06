from __future__ import annotations

__all__ = ["DatapackVersion", "RhombusVersionError", "RhombusEnvironment", "RhombusAddon", "env"]

from typing import Callable, Any, Optional, TYPE_CHECKING
from types import ModuleType
from dataclasses import dataclass, field
from pathlib import Path
import threading

import beet

if TYPE_CHECKING:
    from rhombus.core import DensityFunction
    from rhombus.core.utils import BeetFile

from rhombus.core.utils import GlobalBinding



# ======// Versioning //==========================================================================//

type DatapackVersion = float

class RhombusVersionError(Exception):
    """Exception raised when a function or macro is not supported in the target version."""
    pass


# ======// Environment //=========================================================================//


class RhombusEnvironment:
    _misode_versions_cache: list[dict] | None = None

    def __init__(self):

        # Context
        self.datapack: beet.DataPack | None = None

        # Configuration
        self.datapack_version: DatapackVersion | None = None
        self.strict_versioning: bool = True
        """If True, throws errors when macros/functions are not supported in the target version. If False, warns and tries to use a default."""
        self.deserialize_references_directly: bool = False
        self.infinitesimal: float = 1e-16

        # Registries
        self.density_function_type_deserialization_register: dict[str, type["DensityFunction"]] = {}
        "Mapping of all `DensityFunction` subclasses that are used for deserialization, with their ids as the keys."
        self.caching_function_types: set[type["DensityFunction"]] = set()
        "Set of `DensityFunction` subclasses that apply structuring logic for enabling caching"
        self.preview_beet_file_extensions: set[type["BeetFile"]] = set()
        "Set of `BeetFile` representing datapack files to include when previewing a datapack."  # This was introduces for the CLI, so addons can be stated
        self.preview_file_icons: dict[str, str] = {}
        "Mapping of svg file icons and corresponding Regex expressions that are tested on the registry ids (without namespace)"
        self.preview_scripts: list[str | Path] = []
        """Paths of JavaScript or TypeScript files in this attribute will be loaded by
        Rhombus Preview and patched into Deepslate.

        This could look like this:
        ```
        env.preview_scripts.append(files("rhombus.support.lithostitched").joinpath("deepslate.ts"))
        ```
        """

        self._addons: list[RhombusAddon] = []

        self._reg_lock = threading.RLock()

    def set_version(self, version: str | int | float) -> None:
        """Sets the datapack version. If a string is provided (e.g. '1.21.4'), it is resolved to a datapack version using Misode's data."""
        if isinstance(version, (int, float)):
            self.datapack_version = float(version)
            return

        if RhombusEnvironment._misode_versions_cache is None:
            import urllib.request
            import json
            try:
                with urllib.request.urlopen('https://raw.githubusercontent.com/misode/mcmeta/summary/versions/data.json') as response:
                    RhombusEnvironment._misode_versions_cache = json.loads(response.read().decode('utf-8'))
            except Exception as e:
                raise RuntimeError(f"Failed to fetch version mapping from Misode: {e}")

        for v in RhombusEnvironment._misode_versions_cache:
            if v.get('id') == version:
                if 'data_pack_version' in v:
                    self.datapack_version = float(v['data_pack_version'])
                    return
                else:
                    raise ValueError(f"Version '{version}' does not have a data_pack_version.")
        
        raise ValueError(f"Minecraft version '{version}' not found in Misode data.")

    def load_addons(self, *addons: ModuleType | "RhombusAddon") -> None:
        """Loads addons for Rhombus and calls their individual registration procedures.

        Addon registration typically includes adding custom density function types to the
        decoding register or providing visualization patches for the preview.
        """
        for addon_target in addons:
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
            self._addons.append(addon_obj)


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
        }
    )
    ```

    Parameters:
        name (str): Identifier for the addon
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

    name: str
    density_functions: dict[str, "DensityFunction"] = field(default_factory=dict)
    caching_functions: set["DensityFunction"] = field(default_factory=set)
    preview_scripts: list[str | Path] = field(default_factory=list)
    preview_beet_file_extensions: set["BeetFile"] = field(default_factory=set)
    on_apply: Optional[Callable[["RhombusEnvironment"], Any]] = None

    def apply_to_rhombus_env(self, env: "RhombusEnvironment") -> None:
        if self.on_apply:
            self.on_apply(env)

        env.density_function_type_deserialization_register.update(
            self.density_functions
        )
        env.caching_function_types.update(self.caching_functions)
        env.preview_scripts.extend(self.preview_scripts)
        env.preview_beet_file_extensions.update(self.preview_beet_file_extensions)


# NOTE: rhombus.core should not include runtime relevant symbols.
# Thus 'env' should be moved somewhere else in the future.
env: RhombusEnvironment = GlobalBinding(RhombusEnvironment)
"""The default global Rhombus environment.

For more information on how to use environments see
[`RhombusEnvironment`](https://annhilati.github.io/rhombus/reference/rhombus/core/environment/RhombusEnvironment/).
"""
