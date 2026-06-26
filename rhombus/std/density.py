from __future__ import annotations

__all__ = ["Density", "AnyDensity"]


from dataclasses import dataclass
from typing import Self, Literal, overload
import beet
import beet.contrib.worldgen as beet_worldgen

from rhombus import config
from rhombus.core.density_function import DensityFunction, constant, Reference
from rhombus.core.datapack_resource import DatapackResource
from rhombus.core.utils import JSONDict, BeetFile, uuid_hash, contextfunction, FROM_CONTEXT
from rhombus.std import types


#======// Density Type //========================================================================//

@dataclass
class Density[Function: DensityFunction = DensityFunction]:
    """Class representing a density calculation.
    
    When just using Rhombus for defining density functions, the constructor of this
    class is not needed. To define a new density instead use:
    - Macros from `rhombus.std.functions`, from `rhombus.macros` or other.
    - `.constant()` to create a new Density from any interpretable value.
    - `.refer()` to reference a density function that is provided externally, like by another datapack.
    - `.configured()` to create a value that can be easily altered or referenced in the compiled datapack later.
    - `.partitioned()` to compile a density function to a separate file. This is mainly used to enable caching.
    """

    AST: Function
    "The density function AST represented by this Density."

    def __post_init__(self):
        if not isinstance(self.AST, DensityFunction):
            raise TypeError(f"Cannot initialize Density object with content of type '{type(self.AST).__name__}'")

    def __repr__(self) -> str:
        return self.AST.__repr__()
    

    #======// Factories //=======================================================================//

    @classmethod
    def constant(cls, value: AnyDensity) -> Density:
        """Creates a new `Density` object from any interpretable value.
        
        Allowed are:
            - `float` and `int` numbers
            - `str` references
            - `dict` with the `type` key
            - `Density` objects
            - `DensityFunction` objects
        """
        return _unify(value)
    
    @classmethod
    def refer(cls, identifier: str) -> Density[Reference]:
        """Creates a new `Density` object refering to an externally provided density function."""
        return cls(Reference(identifier))
    
    @classmethod
    def configured(cls, name: str, default: AnyDensity) -> Density[Reference]:
        """Creates a new `Density` object which value that can be easily altered or referenced in the compiled datapack later."""
        caching_types = (types.cache_2d, types.flat_cache, types.cache_all_in_cell, types.cache_once) # TODO: This should not be hardcoded
        name = "minecraft:" + name if not ":" in name else name
        default = Density.constant(default).AST
        if isinstance(default, types.Reference) and isinstance(default.definition, caching_types):
            default = default.definition
        return Density(Reference(name, default))
    
    @classmethod
    def partitioned(cls, value: AnyDensity):
        """Creates a new `Density` object which value will be compiled to a separate file. This is mainly used to enable caching."""
        value = Density.constant(value)
        return Density.configured("rhombus:partitioned/" + uuid_hash(value.as_dict()), value.AST)
    

    #======// Toolchain //=======================================================================//

    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def from_datapack(cls, dp: beet.DataPack, identifier: str) -> Density | None:
        "Creates a `Density` object from a density function in a Beet datapack."

        identifier = "minecraft:" + identifier if not ":" in identifier else identifier

        file = dp[beet_worldgen.WorldgenDensityFunction].get(identifier)
        if file is None:
            return None

        return Density.from_dict(file.data, dp=dp)
    
    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def from_datapack_noise_router(cls,
        dp: beet.DataPack,
        noise_settings: str,
        noise_router: str | Literal[
            "barrier", "continents", "depth", "erosion", "final_density", "fluid_level_floodedness", "fluid_level_spread",
            "lava", "preliminary_surface_level", "ridges", "temperature", "vegetation", "vein_gap", "vein_ridged", "vein_toggle"
        ]
    ) -> Density | None:
        "Creates a `Density` object from a noise router entry of a noise settings file in a Beet datapack."

        identifier = "minecraft:" + noise_settings if not ":" in noise_settings else noise_settings

        file = dp[beet_worldgen.WorldgenNoiseSettings].get(identifier)
        if file is None:
            return None

        if file.data.get("noise_router") is None or file.data.get("noise_router").get(noise_router) is None:
            return None

        return Density.from_dict(file.data["noise_router"][noise_router], dp=dp)
    
    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def from_dict(cls, d: JSONDict, /, dp: beet.DataPack | None = FROM_CONTEXT) -> Density:
        """Creates a `Density` object from a dictionary.
        
        A Beet datapack can be provided as context.
        """
        return Density(DensityFunction.deserialize_toplevel(d))
    
    def compile(self, identifier: str = "main", /) -> dict[str, BeetFile]:
        "Compiles the Density into Beet file class instances."
        files: dict[str, BeetFile] = {}

        for node in self.AST.inscribed_toplevel_nodes:
            if node is self.AST:
                continue
            
            id = node.reference

            files[id] = node.fileclass(node.serialize_toplevel())

        if ":" not in identifier: identifier = "minecraft:" + identifier
        files[identifier] = beet_worldgen.WorldgenDensityFunction(self.AST.serialize_toplevel())

        return files

    def inject(self, dp: beet.DataPack, identifier: str) -> None:
        """Implements the Density and all additionally required files in a datapack.
        """

        files = self.compile(identifier)
        for id, file in files.items():
            dp[id] = file
        
    
    #======// Debug //===========================================================================//
    
    def as_dict(self) -> JSONDict:
        """Only for debugging.<br>Returns the density function AST as a key-value-mapping like it can be used in a density function definition file.<br>
        The dictionary will not be fully inline. References that require separate files will be references."""
        return self.AST.serialize_toplevel()

    def show_in_dir(self, identifier: str = "test"):
        "Only for debugging.<br>Opens a temporary directory with all the compiled files. The directory will be deleted when pressing Enter in the console."
        import sys, os, subprocess, tempfile, pathlib
        
        files = self.compile(identifier)
        
        def open_folder(path: pathlib.Path) -> None:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])

        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)

            for id, file in files.items():
                namespace = id.split(":")[0]
                name = id.split(":")[-1].replace("/", ".")
                path = tmp / (namespace + "." + file.scope[-1] + "." + name + file.extension)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(file.encoder(file.data))

            open_folder(tmp)
            input("Press enter to let go temporary directory ... ")
            
    def __len__(self) -> int:
        from rhombus.macros import performance
        info = performance.get_size(self)
        return info.toplevel_nodes + info.unique_cached_nodes
                

    #======// Arithmetic Magic //================================================================//
    
    def __add__(self, other) -> Density[types.add]:
        other = Density.constant(other).AST
        self = self.AST
        return Density(types.add(self, other))
    
    def __radd__(self, other) -> Density[types.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[types.add]:
        other = Density.constant(other).AST
        self = self.AST
        return Density(
            types.add(
                argument1=self,
                argument2=types.mul(
                    argument1=other,
                    argument2=constant(-1.0)
            )))
    
    def __rsub__(self, other) -> Density[types.add]:
        other = Density.constant(other).AST
        self = self.AST
        return Density(
            types.add(
                argument1=other,
                argument2=types.mul(
                    argument1=self,
                    argument2=constant(-1.0)
            )))
    
    def __mul__(self, other) -> Density[types.mul]:
        other = Density.constant(other).AST
        self = self.AST
        return Density(types.mul(self, other))
    
    def __rmul__(self, other) -> Density[types.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[types.mul]:
        other = Density.constant(other).AST
        self = self.AST
        return Density(types.mul(self, types.invert(other)))
    
    def __rtruediv__(self, other) -> Density[types.mul]:
        other = Density.constant(other).AST
        self = self.AST
        return Density(types.mul(other, types.invert(self)))

    def __floordiv__(self, other):
        from rhombus.macros.math import fastFloordiv
        return fastFloordiv(self, other)
    
    def __rfloordiv__(self, other):
        from rhombus.macros.math import fastFloordiv
        return fastFloordiv(self, other)
        
    def __mod__(self, other):
        from rhombus.macros.math import fastMod
        return fastMod(self, other)

    def __rmod__(self, other):
        from rhombus.macros.math import fastMod
        return fastMod(self, other)
    
    @overload
    def __pow__(self, other: Literal[2]) -> Density[types.square]: ...
    @overload
    def __pow__(self, other: Literal[3]) -> Density[types.cube]: ...
    @overload
    def __pow__(self, other: int) -> Density[types.mul]: ...
    def __pow__(self, other):
        wrapped = self.AST
        if not isinstance(other, int) or other < 0:
            raise ValueError("Can only raise to positive integers")
        if other == 0:
            return Density(types.constant(1))
        elif other == 1:
            return self
        elif other == 2:
            return Density(types.square(wrapped))
        elif other == 3:
            return Density(types.cube(wrapped))
        elif other > 3:
            s = Density(types.mul(wrapped, wrapped))
            for i in range(other - 2):
                s = Density(types.mul(s.AST, wrapped))
            return s

    def __and__(self, other):
        other = Density.constant(other).AST
        self = self.AST
        return Density(types.max(self, other))
    
    def __or__(self, other):
        other = Density.constant(other).AST
        self = self.AST
        return Density(types.min(self, other))
    
    def __abs__(self) -> "Density[types.abs]":
        return Density(types.abs(self.AST))
    
    def __neg__(self) -> Density[types.mul]:
        return Density(types.mul(self.AST, constant(-1.0)))
    
    def __pos__(self) -> Self:
        return self
    

    #======// Logical Magic //===================================================================//
    
    def __eq__(self, other):
        if not isinstance(other, Density):
            return False
        return self.AST == other.AST
    
    def __ne__(self, other): 
        if not isinstance(other, Density):
            return False
        return self.AST != other.AST

    def __gt__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro")
    def __lt__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro")
    def __ge__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro")
    def __le__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro")
    def __bool__(self):      raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro")


#======// AnyDensity //==========================================================================//

type AnyDensity = Density | float | int | str
"Type for denoting that any straightforward Density shorthand can be used."

def _unify(v: int | float | str | Density | DensityFunction) -> Density:
    """Interprets a QoL argument input and returns a Density object.
    Applies logic like splitting large literal constants into calculations
    before constructing constant AST nodes.
    """

    if isinstance(v, Density):
        return v

    if isinstance(v, DensityFunction):
        return Density(v)

    if isinstance(v, (int, float)):
        return Density(constant(float(v)))

    if isinstance(v, str):
        if ":" not in v:
            v = "minecraft:" + v
        return Density(Reference(v))

    raise ValueError(f"Cannot resolve object of type '{type(v).__name__}' to a density function")