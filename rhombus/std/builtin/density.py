from __future__ import annotations

__all__ = ["Density", "AnyDensity"]

from dataclasses import dataclass
from typing import Any, Self, Literal, overload
import re

import beet
import beet.contrib.worldgen as beet_worldgen

from rhombus.core.abstract import RhombusASTNode
from rhombus.core.models import DatapackNode, DensityFunction, constant, Reference, transform
from rhombus.core.utils import JSONDict, BeetFile, JSON_hash
from rhombus.runtime import datapack_handler, rho


type AnyDensity = Density | RhombusASTNode[DensityFunction] | DensityFunction | float | int | str
"Type for denoting that any straightforward shorthand for a density function value can be used."


@dataclass(frozen=False)
class Density:
    """The **`Density`** class is the central type that represents a density function.

    ## Creation
    Primitive density values can be constructed from various types:
    - literal numbers for constant values,
    - strings for references,
    - other `Density`, `DensityFunction` or `RhombusASTNode` objects.

    To create a `Density` object from a dictionary, use `~.from_dict()` instead
    of the constructor.

    ## Naming & Partitioning
    By default, file names are generated randomly (based on the content).
    Although an identifier can be assigned to a `Density` object to facilitate
    debugging or to provide configurable values or compatability with other packs:

        df = Density(5).named("minecraft:my_variable")

    Naming a density function partitiones it from the otherwise monolithic
    density function tree. To partition without naming use `Density.partitioned()`.
    """

    AST: RhombusASTNode[DensityFunction]
    "The abstract syntax tree of macros of the density."

    # remove overloads to remove clutter?
    @overload
    def __init__(self, reference: str): ...
    @overload
    def __init__(self, constant: int | float): ...
    @overload
    def __init__(self, d: Density): ...
    @overload
    def __init__(self, ast: RhombusASTNode[DensityFunction] | DensityFunction): ...
    @overload
    def __init__(self, arg: AnyDensity): ...
    def __init__(self, *args: AnyDensity, **kwargs):
        if len(args) == len(kwargs.values()) == 0:
            raise TypeError("Density() takes exactly one argument (0 given)")
        arg = (list(args) + list(kwargs.values()))[0]

        if isinstance(arg, Density):
            self.AST = arg.AST

        elif isinstance(arg, RhombusASTNode):
            self.AST = arg

        elif isinstance(arg, DensityFunction):
            self.AST = RhombusASTNode.value(arg)

        elif isinstance(arg, (int, float)):
            self.AST = RhombusASTNode.value(constant(float(arg)))
    
        elif isinstance(arg, str):
            if ":" not in arg:
                arg = "minecraft:" + arg
            definition = None
            if rho.fetch_reference_definition_from_context and rho.datapack is not None:
                definition = rho.datapack[beet_worldgen.WorldgenDensityFunction].get(arg)
            self.AST = RhombusASTNode.value(
                Reference(arg, definition=DensityFunction.deserialize_toplevel(definition.data) if definition is not None else None)
            )
    
        else:
            raise ValueError(
                f"Cannot resolve object of type {type(arg).__name__} to a density function"
            )

    def __repr__(self) -> str:
        return self.AST.__repr__()
    
    def __hash__(self) -> int:
            return hash(self.AST)


    # ======// Factories //======================================================================//

    def named(self, identifier: str, /) -> Self:
        """Specifies a resource identifier with which the density function will be compiled."""
        if not isinstance(identifier, str):
            raise TypeError("identifier has to be of string type")
        identifier = "minecraft:" + identifier if ":" not in identifier else identifier

        def build_reference() -> Reference:
            df_build = self.build()
            df_build = self._unwrap_nested_partitions(df_build)
            return Reference(identifier, definition=df_build)

        def repr(node: RhombusASTNode[Reference]) -> str:
            val = getattr(self.AST, "_value", None)
            if isinstance(val, constant):
                return f"Density({val.value!r}).named(\"{identifier}\")"
            if isinstance(val, Reference):
                return f"Density(\"{val.identifier}\").named(\"{identifier}\")"

            s = f"{self!r}"
            try:
                f_val = float(s)
                return f"Density({f_val!r}).named(\"{identifier}\")"
            except (ValueError, TypeError):
                pass

            if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
                inner = s[1:-1]
                if re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", inner):
                    return f"Density(\"{inner}\").named(\"{identifier}\")"

            return f"{self!r}.named(\"{identifier}\")"

        return Density(RhombusASTNode.defer(build_reference, repr=repr))


    # TODO: make this an instance method?
    @classmethod
    def partitioned(cls, value: AnyDensity) -> Density:
        """Creates a new `Density` object which value will be compiled to a separate file.
        This is mainly used to enable caching in older versions.
        """
        def build_partitioned() -> Reference:
            df_build = Density(value).build()
            df_build = cls._unwrap_nested_partitions(df_build)
            h = JSON_hash(df_build.serialize_toplevel())
            return Reference(f"rhombus:generated/{h}", definition=df_build)

        return Density(RhombusASTNode.defer(build_partitioned, repr=lambda n: value.__repr__()))


    @staticmethod
    def _unwrap_nested_partitions(df: DensityFunction) -> DensityFunction:
        """Inlines intermediate auto-generated references (such as nested caching functions)
        into the current node so they do not produce redundant separate files.
        """
        import rhombus.library.vanilla.types as vt
        import rhombus.library.vanilla.legacy_types as lt

        caching_types = (
            vt.cache,
            lt.cache_2d,
            lt.flat_cache,
            lt.cache_all_in_cell,
            lt.interpolated,
        )

        while (
            isinstance(df, Reference)
            and df.target.startswith("rhombus:generated/")
            and df.definition is not None
        ):
            df = df.definition

        def _unwrap_caching_references(n: DatapackNode) -> DatapackNode:
            if (
                isinstance(n, Reference)
                and n.target.startswith("rhombus:generated/")
                and isinstance(n.definition, caching_types)
            ):
                return n.definition
            return n

        return transform(df, _unwrap_caching_references)


    @classmethod
    def from_dict(cls, dict: JSONDict) -> Density:
        """Creates a `Density` object from a density function definition dictionary."""
        return Density(RhombusASTNode.defer(lambda: DensityFunction.deserialize_toplevel(dict)))


    @classmethod
    @datapack_handler
    def from_datapack(cls, dp: beet.DataPack, identifier: str) -> Density | None:
        """Creates a `Density` object from a density function in a Beet datapack.
        
        Parameters:
            dp (DataPack): A Beet datapack.
            identifier (str): Resource identifier of the density function.

        Returns:
            Density: The density function as a `Density` object if it is present in the datapack.
            None: otherwise. (won't raise if no density function is present)
        """

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
        """Creates a `Density` object from a noise router entry from noise settings in a Beet datapack.
        
        Parameters:
            dp (DataPack): A Beet datapack.
            noise_settings (str): Resource identifier of the noise settings.
            noise_router (str): Noise router entry with a density function.

        Returns:
            Density: The noise router entry as a `Density` object if it is present in the datapack.
            None: otherwise. (won't raise if no noise router entry is present)
        """

        identifier = (
            "minecraft:" + noise_settings
            if ":" not in noise_settings
            else noise_settings
        )

        file = dp[beet_worldgen.WorldgenNoiseSettings].get(identifier)

        if (
            file is None
            or file.data.get("noise_router") is None
            or file.data.get("noise_router").get(noise_router) is None
        ):
            return None

        return Density.from_dict(file.data["noise_router"][noise_router])


# ======// Processing //=========================================================================//

    def build(self) -> DensityFunction:
        """Builds a `DensityFunction` data model from the `Density` object.
        
        Lazy macros will be resolved. Thus the result depends on the datapack
        and mod versions **currently** present in the environment.
        """
        return self.AST.build()

    def compile(self, identifier: str = "main") -> set[tuple[str, BeetFile]]:
        """Compiles the `Density` into Beet file instances.
        
        **TIP:** To process the file data without using Beet see the `BeetFile` protocol.
        """
        files: set[tuple[str, BeetFile]] = set()

        if ":" not in identifier:
            identifier = "minecraft:" + identifier

        df_build = self.build()

        for node in df_build.inscribed_toplevel_nodes:
            id = node.identifier
            if id != identifier:
                if node.fileclass is None:
                    raise TypeError(
                        f"Cannot compile Density. Node class '{node.__class__}' is missing class variable 'fileclass'"
                    )
                if id != df_build.identifier or not id.startswith("rhombus:generated/"):
                    files.add((id, node.fileclass(node.serialize_toplevel())))

        files.add(
            (
                identifier,
                beet_worldgen.WorldgenDensityFunction(df_build.serialize_toplevel()),
            )
        )

        return files

    def implement(self, dp: beet.DataPack, identifier: str) -> None:
        """Implements the Density and all additional required files in a datapack."""

        files = self.compile(identifier)
        for id, file in files:
            dp[id] = file


    # ======// Indev //===========================================================================//

    def as_dict(self) -> JSONDict:
        """Builds the density function model and returns the top-level as a dictionary."""
        return self.build().serialize_toplevel()
    
    def info(self):
        """Build the density function model and Provides information about the number of nodes it contains."""
        from rhombus.engine import df_size_info
        return df_size_info(self.build())


    # =====// Safety //==========================================================================//

    @classmethod
    def is_any_density(cls, v: AnyDensity | Any) -> bool:
        try:
            cls(v)
            return True
        except:
            return False

    @overload
    def is_of_type(self) -> DensityFunction: ...
    @overload
    def is_of_type(self, t: DensityFunction) -> bool: ...
    def is_of_type(self, *args):
        if len(args) == 0:
            return type(self.build())
        return isinstance(self.build(), args[0])


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
            
        cond._truthy_eval_fallback = _fallback
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