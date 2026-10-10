from __future__ import annotations

__all__ = ["Density", "AnyDensity"]


from dataclasses import dataclass
from typing import Any, Self, Literal, overload, TYPE_CHECKING

import beet
import beet.contrib.worldgen as beet_worldgen

from rhombus.core.abstract import RhombusASTNode, lazy
from rhombus.core.models.density_function import DensityFunction, constant, Reference
from rhombus.core.utils import JSONDict, BeetFile, JSON_hash
from rhombus.core.environment import DatapackVersion
from rhombus.runtime import datapack_handler, rho, FROM_CONTEXT

if TYPE_CHECKING:
    from rhombus.std._implementations.optimization import DensityFunctionSizeInfo


# ======// Density Type //========================================================================//


@dataclass(frozen=False)
class Density:
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

    AST: RhombusASTNode[DensityFunction]
    "The density function AST represented by this Density."

    @overload
    def __init__(self, reference: str): ...
    @overload
    def __init__(self, value: int | float): ...
    @overload
    def __init__(self, ast: Density): ...
    @overload
    def __init__(self, ast: RhombusASTNode[DensityFunction] | DensityFunction): ...
    @overload
    def __init__(self, arg: AnyDensity): ...
    def __init__(self, arg: AnyDensity):
        if isinstance(arg, Density):
            self.AST = arg.AST

        elif isinstance(arg, RhombusASTNode):
            self.AST = arg

        elif isinstance(arg, DensityFunction):
            self.AST = _lazy_node(arg)

        elif isinstance(arg, (int, float)):
            self.AST = _lazy_node(constant(float(arg)))
    
        elif isinstance(arg, str):
            if ":" not in arg:
                arg = "minecraft:" + arg
            self.AST = _lazy_node(Reference(arg)) # TODO: Fetch datapack context here?
    
        else:
            raise ValueError(
                f"Cannot resolve object of type {type(arg).__name__!r} to a density function"
            )

    def __repr__(self) -> str:
        return self.AST.__repr__()

    # ======// Factories //=======================================================================//

    @classmethod
    def _configured(cls, identifier: str, value: AnyDensity):
        if not isinstance(identifier, str):
            raise TypeError("identifier has to be of string type")
        value = Density(value)
        identifier = "minecraft:" + identifier if ":" not in identifier else identifier
        
        @lazy
        def _lazy_reference(target: str, definition: Any):
            from rhombus.core.models.density_function import Reference
            return Reference(target, definition=definition.build())

        return Density(_lazy_reference(identifier, value.AST))

    @classmethod
    def partitioned(cls, value: AnyDensity) -> Density:
        """Creates a new `Density` object which value will be compiled to a separate file. This is mainly used to enable caching."""
        return Density._configured(
            identifier="rhombus:generated/" + JSON_hash(Density(value).as_dict()),
            value=value
        )

    def __rmatmul__(self, identifier: str):
        import rhombus.support.vanilla.types as vt
        
        default = self.AST
        if isinstance(default, Reference) and isinstance(default.definition, vt.cache):
            default = default.definition
        return Density._configured(identifier, default)


    # ======// Toolchain //=======================================================================//

    @classmethod
    @datapack_handler
    def from_dict(
        cls, d: JSONDict, /, dp: beet.DataPack | None = FROM_CONTEXT
    ) -> Density:
        """Creates a `Density` object from a dictionary.

        A Beet datapack can be provided as context.
        """
        return Density(DensityFunction.deserialize_toplevel(d))

    @classmethod
    @datapack_handler
    def from_datapack(cls, dp: beet.DataPack, identifier: str) -> Density | None:
        "Creates a `Density` object from a density function in a Beet datapack."

        identifier = "minecraft:" + identifier if ":" not in identifier else identifier

        file = dp[beet_worldgen.WorldgenDensityFunction].get(identifier)
        if file is None:
            return None

        return Density.from_dict(file.data, dp=dp)

    @classmethod
    @datapack_handler
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

    def compile(self, identifier: str = "main", /, *, version: DatapackVersion = ...) -> set[tuple[str, BeetFile]]:
        """Compiles the Density into Beet file class instances.
        
        See the `BeetFile` protocol to find out how to use the file data without using Beet.
        """
        
        old_datapack_version = rho.datapack_version
        if version is not ...:
            rho.datapack_version = version

        files: set[tuple[str, BeetFile]] = set()

        if ":" not in identifier:
            identifier = "minecraft:" + identifier

        df = self.AST.build()

        for node in df.inscribed_toplevel_nodes:
            id = node.identifier
            if id != identifier:
                if node.fileclass is None:
                    raise TypeError(
                        f"Cannot compile Density. Node class '{node.__class__}' is missing class variable 'fileclass'"
                    )
                if id != df.identifier or not id.startswith("rhombus:generated/"):
                    files.add((id, node.fileclass(node.serialize_toplevel())))

        files.add(
            (
                identifier,
                beet_worldgen.WorldgenDensityFunction(df.serialize_toplevel()),
            )
        )

        rho.datapack_version = old_datapack_version

        return files

    def implement(self, dp: beet.DataPack, identifier: str) -> None:
        """Implements the Density and all additional required files in a datapack."""

        files = self.compile(identifier)
        for id, file in files:
            dp[id] = file


    # ======// Debug //===========================================================================//

    def as_dict(self) -> JSONDict:
        """Returns the density function AST as a key-value-mapping like it can be used in a density function definition file.
        The dictionary will not be fully inline. References that require separate files will be references."""
        return self.AST.build().serialize_toplevel()
    
    def info(self) -> DensityFunctionSizeInfo:
        from rhombus.std._implementations.optimization import df_size_info
        return df_size_info(self.AST.build())

    # ======// Arithmetic Magic //================================================================//

    def __add__(self, other) -> Density:
        from rhombus.std.math.general import add
        return add(self, other)

    def __radd__(self, other) -> Density:
        return self.__add__(other)

    def __sub__(self, other) -> Density:
        from rhombus.std.math.general import sub
        return sub(self, other)

    def __rsub__(self, other) -> Density:
        from rhombus.std.math.general import sub
        return sub(other, self)

    def __mul__(self, other) -> Density:
        from rhombus.std.math.general import mul
        return mul(self, other)  

    def __rmul__(self, other) -> Density:
        return self.__mul__(other)

    def __truediv__(self, other) -> Density:
        from rhombus.std.math.general import div
        return div(self, other)

    def __rtruediv__(self, other):
        from rhombus.std.math.general import div
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

    def __pow__(self, other):
        from rhombus.std.math import pow
        return pow(self, other)

    def __rpow__(self, other):
        from rhombus.std.math import pow
        return pow(other, self)

    def __and__(self, other):
        from rhombus.std.math import max
        return max(other, self)

    def __or__(self, other):
        from rhombus.std.math import min
        return min(other, self)

    def __abs__(self) -> Density:
        from rhombus.std.math import abs
        return abs(self)

    def __neg__(self) -> Density:
        from rhombus.std.math import neg
        return neg(self)
        
    def __pos__(self) -> Self:
        return self

    # ======// Logical Magic //===================================================================//

    def __eq__(self, other):
        from rhombus.std.conditional.fluent import when
        cond = when(self).equals(other)
        
        def _fallback():
            if hasattr(other, "AST"):
                return self.AST == other.AST
            return False
            
        object.__setattr__(cond, "_truthy_eval_fallback", _fallback)
        return cond

    def __ne__(self, other):
        from rhombus.std.conditional.fluent import when
        cond = when(self).unequals(other)
        
        def _fallback():
            if hasattr(other, "AST"):
                return self.AST != other.AST
            return True
            
        object.__setattr__(cond, "_truthy_eval_fallback", _fallback)
        return cond

    def __gt__(self, other):
        from rhombus.std.conditional.fluent import when
        return when(self).greater(other)

    def __lt__(self, other):
        from rhombus.std.conditional.fluent import when
        return when(self).less(other)

    def __ge__(self, other):
        from rhombus.std.conditional.fluent import when
        return when(self).atleast(other)

    def __le__(self, other):
        from rhombus.std.conditional.fluent import when
        return when(self).atmost(other)

    # def __bool__(self):
    #     raise NotImplementedError(
    #         "Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro"
    #     )


# ======// AnyDensity //==========================================================================//

type AnyDensity = Density | RhombusASTNode[DensityFunction] | DensityFunction | float | int | str
"Type for denoting that any straightforward Density shorthand can be used."


@lazy
def _lazy_node(val: Any) -> Any:
    return val