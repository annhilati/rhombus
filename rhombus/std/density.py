from __future__ import annotations

__all__ = ["Density", "AnyDensity"]


from dataclasses import dataclass
from typing import Self, Literal, overload
import beet
import beet.contrib.worldgen as beet_worldgen

from rhombus.core.density_function import DensityFunction, constant, Reference
from rhombus.core.utils import (
    JSONDict,
    BeetFile,
    uuid_hash,
    contextfunction,
    FROM_CONTEXT,
)
from rhombus.core.environment import env
from rhombus.support import vanilla as vt


# ======// Density Type //========================================================================//


@dataclass(frozen=False)
class Density[Function: DensityFunction = DensityFunction]:
    """The **`Density`** class is the main interface for writing density functions
    with Rhombus.

    The `Density()` constructor accepts arguments of various types:
    - `int` and `float` for constant values
    - `str` for references
    - `Density` and `DensityFunction`

    It does not accept `dict` objects, as they are ambiguous and can be interpreted
    in multiple ways. To deserialize such, use `~.from_dict()` instead.

    By default, file names for density functions are not chosen but generated. To allow
    users to configure your datapack or let other datapacks hook into your datapack, you
    can set a fixed name through this idiom:
    ```
    df = "minecraft:my_variable" @ Density(5)
    ```
    """

    AST: Function
    "The density function AST represented by this Density."

    @overload
    def __init__(self, reference: str): ...
    @overload
    def __init__(self, value: int | float): ...
    @overload
    def __init__(self, ast: Function | Density[Function]): ...
    @overload
    def __init__(self, arg: AnyDensity): ...
    def __init__(self, arg: AnyDensity):
        self.AST = _unify(arg)

    def __repr__(self) -> str:
        return self.AST.__repr__()

    # ======// Factories //=======================================================================//

    @classmethod
    def partitioned(cls, value: AnyDensity) -> Density[Reference]:
        """Creates a new `Density` object which value will be compiled to a separate file. This is mainly used to enable caching."""
        value = Density(value)
        return ("rhombus:partitioned/" + uuid_hash(value.as_dict())) @ value

    def __rmatmul__(self, identifier: str):
        if not isinstance(identifier, str):
            raise TypeError("Density can only be assigned to a string identifier")
        identifier = "minecraft:" + identifier if ":" not in identifier else identifier
        default = self.AST
        if isinstance(default, vt.Reference) and isinstance(
            default.definition, tuple(env.caching_function_types)
        ):
            default = default.definition
        return Density(Reference(identifier, default))

    # ======// Toolchain //=======================================================================//

    @classmethod
    @contextfunction(dp="datapack")
    def from_dict(
        cls, d: JSONDict, /, dp: beet.DataPack | None = FROM_CONTEXT
    ) -> Density:
        """Creates a `Density` object from a dictionary.

        A Beet datapack can be provided as context.
        """
        return Density(DensityFunction.deserialize_toplevel(d))

    @classmethod
    @contextfunction(dp="datapack")
    def from_datapack(cls, dp: beet.DataPack, identifier: str) -> Density | None:
        "Creates a `Density` object from a density function in a Beet datapack."

        identifier = "minecraft:" + identifier if ":" not in identifier else identifier

        file = dp[beet_worldgen.WorldgenDensityFunction].get(identifier)
        if file is None:
            return None

        return Density.from_dict(file.data, dp=dp)

    @classmethod
    @contextfunction(dp="datapack")
    def from_datapack_noise_router(
        cls,
        dp: beet.DataPack,
        noise_settings: str,
        noise_router: str
        | Literal[
            "barrier",
            "continents",
            "depth",
            "erosion",
            "final_density",
            "fluid_level_floodedness",
            "fluid_level_spread",
            "lava",
            "preliminary_surface_level",
            "ridges",
            "temperature",
            "vegetation",
            "vein_gap",
            "vein_ridged",
            "vein_toggle",
        ],
    ) -> Density | None:
        "Creates a `Density` object from a noise router entry of a noise settings file in a Beet datapack."

        identifier = (
            "minecraft:" + noise_settings
            if ":" not in noise_settings
            else noise_settings
        )

        file = dp[beet_worldgen.WorldgenNoiseSettings].get(identifier)
        if file is None:
            return None

        if (
            file.data.get("noise_router") is None
            or file.data.get("noise_router").get(noise_router) is None
        ):
            return None

        return Density.from_dict(file.data["noise_router"][noise_router], dp=dp)

    def compile(self, identifier: str = "main", /) -> set[tuple[str, BeetFile]]:
        "Compiles the Density into Beet file class instances."
        files: set[tuple[str, BeetFile]] = set()

        if ":" not in identifier:
            identifier = "minecraft:" + identifier

        for node in self.AST.inscribed_toplevel_nodes:
            id = node.identifier
            if id != identifier:
                if node.fileclass is None:
                    raise TypeError(
                        f"Cannot compile Density. Node class '{node.__class__}' is missing class variable 'fileclass'"
                    )
                files.add((id, node.fileclass(node.serialize_toplevel())))

        files.add(
            (
                identifier,
                beet_worldgen.WorldgenDensityFunction(self.AST.serialize_toplevel()),
            )
        )

        return files

    def implement(self, dp: beet.DataPack, identifier: str) -> None:
        """Implements the Density and all additionally required files in a datapack."""

        files = self.compile(identifier)
        for id, file in files:
            dp[id] = file

    # ======// Debug //===========================================================================//

    def as_dict(self) -> JSONDict:
        """Only for debugging.<br>Returns the density function AST as a key-value-mapping like it can be used in a density function definition file.<br>
        The dictionary will not be fully inline. References that require separate files will be references."""
        return self.AST.serialize_toplevel()

    # ======// Arithmetic Magic //================================================================//

    def __add__(self, other) -> Density[vt.add]:
        return Density(vt.add(self.AST, Density(other).AST))

    def __radd__(self, other) -> Density[vt.add]:
        return self.__add__(other)

    def __sub__(self, other) -> Density[vt.add]:
        from rhombus.std.math import sub

        return sub(self, other)

    def __rsub__(self, other) -> Density[vt.add]:
        from rhombus.std.math import sub

        return sub(other, self)

    def __mul__(self, other) -> Density[vt.mul]:
        return Density(vt.mul(self.AST, Density(other).AST))

    def __rmul__(self, other) -> Density[vt.mul]:
        return self.__mul__(other)

    def __truediv__(self, other) -> Density[vt.mul]:
        from rhombus.std.math import div

        return div(self, other)

    def __rtruediv__(self, other) -> Density[vt.mul]:
        from rhombus.std.math import div

        return div(other, self)

    def __floordiv__(self, other):
        from rhombus.std.math import floordiv

        return floordiv(self, other)

    def __rfloordiv__(self, other):
        from rhombus.std.math import floordiv

        return floordiv(other, self)

    def __mod__(self, other):
        from rhombus.std.math import mod

        return mod(self, other)

    def __rmod__(self, other):
        from rhombus.std.math import mod

        return mod(other, self)

    def __pow__(self, other) -> Density[vt.pow]:
        from rhombus.std.math import pow

        return pow(self, other)

    def __rpow__(self, other) -> Density[vt.pow]:
        from rhombus.std.math import pow

        return pow(other, self)

    def __and__(self, other):
        return Density(vt.max(self.AST, Density(other).AST))

    def __or__(self, other):
        return Density(vt.min(self.AST, Density(other).AST))

    def __abs__(self) -> Density[vt.abs]:
        return Density(vt.abs(self.AST))

    def __neg__(self) -> Density[vt.mul]:
        if env.datapack_version < 111:
            return self * -1
        return Density(vt.negate(self.AST))

    def __pos__(self) -> Self:
        return self

    # ======// Logical Magic //===================================================================//

    def __eq__(self, other):
        if not isinstance(other, Density):
            return False
        return self.AST == other.AST

    def __ne__(self, other):
        if not isinstance(other, Density):
            return False
        return self.AST != other.AST

    # IDEA: Allow building Conditions here -> when needs to become a function to allow conditions and subjects
    def __gt__(self, other):
        raise NotImplementedError(
            "Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro"
        )

    def __lt__(self, other):
        raise NotImplementedError(
            "Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro"
        )

    def __ge__(self, other):
        raise NotImplementedError(
            "Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro"
        )

    def __le__(self, other):
        raise NotImplementedError(
            "Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro"
        )

    def __bool__(self):
        raise NotImplementedError(
            "Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro"
        )


# ======// AnyDensity //==========================================================================//

type AnyDensity = Density | float | int | str
"Type for denoting that any straightforward Density shorthand can be used."


def _unify(v: int | float | str | Density | DensityFunction) -> DensityFunction:
    """Interprets a QoL argument input and returns a DensityFunction object.
    Applies logic like splitting large literal constants into calculations
    before constructing constant AST nodes.
    """

    if isinstance(v, Density):
        return v.AST

    if isinstance(v, DensityFunction):
        return v

    if isinstance(v, (int, float)):
        return constant(float(v))

    if isinstance(v, str):
        if ":" not in v:
            v = "minecraft:" + v
        return Reference(v)

    raise ValueError(
        f"Cannot resolve object of type '{v.__class__.__name__}' to a density function AST"
    )
