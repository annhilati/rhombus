"""
In Rhombus, the abstract syntax trees of composed density functions are
wrapped in instances of the `Density` class, which is defined here.

For more information, see the `.Density` class.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Self, Literal, overload
import beet
import beet.contrib.worldgen as beet_worldgen

from rhombus import config
from rhombus.core.density_function import DensityFunction, constant, Reference
from rhombus.core.dsl.DSLType import DSLType
from rhombus.core.utils import JSONDict, BeetFile, uuid_hash, contextfunction, FROM_CONTEXT
from rhombus.std import vdft

__all__ = ["Density", "ref", "AnyDensity"]


#======// Density Type //========================================================================//

@dataclass
class Density[Function: DensityFunction = DensityFunction]:
    """Class representing a density calculation.
    
    For Rhombus language users, the constructor of this class is not needed. To define a new density instead use:
    - Methods from `rhombus.language.functions` or other methods that return a `Density` for calculations.
    - `.constant()`
    - `.configured()` if a value is needed that can be easily altered in the compiled datapack later.
    - `.partitioned()` if a density function has to be compiled to a separate file, but it is not important what this file is.
    - `.reference()` to reference a density function that is provided externally, like by another datapack.
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
        """Creates a Density constant to a float value or another descriptive value."""
        return AnyDensity.unify(value)
    
    @classmethod
    def refer(cls, identifier: str) -> Density[Reference]:
        """Creates a Density refering to an externally provided density function."""
        return cls(Reference(identifier))
    
    @classmethod
    def configured(cls, name: str, default: AnyDensity) -> Density[Reference]:
        """Creates a Density that will be casted into a specific file when compiling."""
        name = "minecraft:" + name if not ":" in name else name
        default = AnyDensity.unify(default).AST # somehow neccesarry
        return Density(Reference(name, default))
    
    @classmethod
    def partitioned(cls, value: AnyDensity):
        """Creates a Density whose value will be casted into a separate file when compiling."""
        value = AnyDensity.unify(value) # somehow not possible by decorator
        return Density(Reference(
            reference="rhombus:generated/" + uuid_hash(value.as_dict()),
            definition=value.AST)
        )
    

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
    def from_dict(cls, d: JSONDict, /, dp: beet.DataPack | None = FROM_CONTEXT) -> Density:
        """Creates a `Density` object from a dictionary.
        
        A Beet datapack can be provided as context.
        """
        return Density(DensityFunction.deserialize_toplevel(d))
    
    def compile(self, identifier: str, /) -> dict[str, BeetFile]:
        "Compiles the Density into Beet file class instances."
        files: dict[str, BeetFile] = {}

        if ":" not in identifier: identifier = "minecraft:" + identifier

        files[identifier] = beet_worldgen.WorldgenDensityFunction(self.AST.serialize_toplevel())
        files |= self.AST.additional_described_files()

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
                

    #======// Arithmetic Magic //================================================================//
    
    def __add__(self, other) -> Density[vdft.add]:
        other = AnyDensity.unify(other).AST
        self = self.AST
        return Density(vdft.add(self, other))
    
    def __radd__(self, other) -> Density[vdft.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[vdft.add]:
        other = AnyDensity.unify(other).AST
        self = self.AST
        return Density(
            vdft.add(
                argument1=self,
                argument2=vdft.mul(
                    argument1=other,
                    argument2=constant(-1.0)
            )))
    
    def __rsub__(self, other) -> Density[vdft.add]:
        other = AnyDensity.unify(other).AST
        self = self.AST
        return Density(
            vdft.add(
                argument1=other,
                argument2=vdft.mul(
                    argument1=self,
                    argument2=constant(-1.0)
            )))
    
    def __mul__(self, other) -> Density[vdft.mul]:
        other = AnyDensity.unify(other).AST
        self = self.AST
        return Density(vdft.mul(self, other))
    
    def __rmul__(self, other) -> Density[vdft.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[vdft.mul]:
        other = AnyDensity.unify(other).AST
        self = self.AST
        return Density(vdft.mul(self, vdft.invert(other)))
    
    def __rtruediv__(self, other) -> Density[vdft.mul]:
        other = AnyDensity.unify(other).AST
        self = self.AST
        return Density(vdft.mul(other, vdft.invert(self)))
    
    @overload
    def __pow__(self, other: Literal[2]) -> Density[vdft.square]: ...
    @overload
    def __pow__(self, other: Literal[3]) -> Density[vdft.cube]: ...
    @overload
    def __pow__(self, other: int) -> Density[vdft.mul]: ...
    def __pow__(self, other):
        wrapped = self.AST
        if not isinstance(other, int):
            raise ValueError("Can't raise to non-integer powers")
        if other == 0:
            return Density(vdft.constant(1))
        elif other == 1:
            return self
        elif other == 2:
            return Density(vdft.square(wrapped))
        elif other == 3:
            return Density(vdft.cube(wrapped))
        elif other > 3:
            s = Density(vdft.mul(wrapped, wrapped))
            for i in range(other - 2):
                s = Density(vdft.mul(s.AST, wrapped))
            return s

    def __and__(self, other):
        other = AnyDensity.unify(other).AST
        self = self.AST
        return Density(vdft.max(self, other))
    
    def __or__(self, other):
        other = AnyDensity.unify(other).AST
        self = self.AST
        return Density(vdft.min(self, other))
    
    def __abs__(self) -> "Density[vdft.abs]":
        return Density(vdft.abs(self.AST))
    
    def __neg__(self) -> Density[vdft.mul]:
        return Density(vdft.mul(self.AST, constant(-1.0)))
    
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
    def __bool__(self): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro")


#======// AnyDensity //==========================================================================//

class AnyDensity(DSLType, Density):
    "DSL Type"
    
    @classmethod
    def unify(cls, v: int | float | str | Density | DensityFunction, **kwargs) -> Density:
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


def ref(identifier: str, /) -> Density[Reference]:
    "Creates a Density that is a reference to an externally provided density function."
    return Density.refer(identifier)