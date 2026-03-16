"""
In Rhombus, the abstract syntax trees of composed density functions are
wrapped in instances of the `Density` class, which is defined here.

For more information, see the `.Density` class.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Self, Callable, TypeAliasType, Union, Literal, overload, get_args, get_origin
from types import UnionType
import inspect, functools
import beet
import beet.contrib.worldgen as beet_worldgen

from rhombus import config
from rhombus.core.density_function import DensityFunction, constant, Reference
from rhombus.core.utils import JSONDict, Decorator, BeetFileClass, uuid_hash, contextfunction, FROM_CONTEXT
from rhombus.core.codec import decode_HOLDER_HELPER_CODEC
from rhombus.core.compiler import compile
from rhombus.language import types as types

__all__ = ["Density", "DensityDescriptor", "ref"]


type DensityDescriptor = Union[Density, DensityFunction, str, float]
"TypeAliasType for all types that can be interpreted by `resolve_DensityDescriptor()`."

def resolve_DensityDescriptor(arg: DensityDescriptor) -> Density:
    """Interprets a QoL argument input and returns a Density object.
    Applies logic like splitting large literal constants into calculations
    before constructing constant AST nodes.
    """

    limit = config.constant_number_limit

    if isinstance(arg, (int, float)):
        v = float(arg)

        if abs(v) <= limit:
            return Density(constant(v))

        sign = -1.0 if v < 0 else 1.0
        v = abs(v)

        factors: list[float] = []
        while v > limit:
            factors.append(float(limit))
            v /= limit

        factors.append(v * sign)

        it = iter(constant(f) for f in factors)
        result = types.mul(next(it), next(it))
        for x in it:
            result = types.mul(result, x)

        return Density(result)

    if isinstance(arg, Density):
        return arg

    if isinstance(arg, DensityFunction):
        return Density(arg)

    if isinstance(arg, str):
        if ":" not in arg:
            arg = "minecraft:" + arg
        return Density(Reference(arg))

    raise ValueError(f"Cannot resolve object of type '{type(arg)}' to a density function")


def WizardFactory(*, unwrap: bool = False) -> Decorator:
    
    def _apply_by_annotation(annotation: type) -> bool:
        if annotation is DensityDescriptor:
            return True
        if get_origin(annotation) in [Union, UnionType]:
            args = get_args(annotation)
            if Density in args and any([t in args for t in [str, float, int]]):
                return True
        if isinstance(annotation, TypeAliasType):
            return _apply_by_annotation(annotation.__value__)
        return False

    def decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)
        
        params_to_resolve = {
            name for name, param in sig.parameters.items()
            if _apply_by_annotation(param.annotation)
        }

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for name in params_to_resolve:
                if name in bound.arguments:
                    current_val = bound.arguments[name]
                    resolved = resolve_DensityDescriptor(current_val)

                    if unwrap:
                        bound.arguments[name] = resolved.AST
                    else:
                        bound.arguments[name] = resolved

            return func(*bound.args, **bound.kwargs)

        wrapper.__signature__ = sig
        return wrapper

    return decorator

def MacroWizard[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    "Shortcut for `WizardFactory(unwrap=False)`"
    return WizardFactory(unwrap=False)(fn)

def BuiltinWizard[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    "Shortcut for `WizardFactory(unwrap=True)`"
    return WizardFactory(unwrap=True)(fn)


#======// Density Type //========================================================================//

@dataclass
class Density[Function: DensityFunction = DensityFunction]:
    """Class representing a density calculation.
    
    For Rhombus language users, the constructor of this class is not needed. To define a new density instead use:
    - Methods from `rhombus.language.builtins` or other methods that return a `Density` for calculations.
    - `.constant()`
    - `.configured()` if a value is needed that can be easily altered in the compiled datapack later.
    - `.separated()` if a density function has to be compiled to a separate file, but it is not important what this file is.
    - `.referenced()` to reference a density function that is provided externally, like by another datapack.
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
    def constant(cls, value: DensityDescriptor) -> Density:
        """Creates a Density constant to a float value or another descriptive value."""
        return resolve_DensityDescriptor(value)
    
    @classmethod
    def configured(cls, name: str, default: DensityDescriptor) -> Density[Reference]:
        """Creates a Density that will be casted into a specific file when compiling."""
        name = "minecraft:" + name if not ":" in name else name
        default = resolve_DensityDescriptor(default).AST # somehow neccesarry
        if isinstance(default, Reference):
            default = types.add(default, 0)
        return Density(Reference(name, default))
    
    @classmethod
    def separated(cls, value: DensityDescriptor):
        """Creates a Density whose value will be casted into a separate file when compiling."""
        value = resolve_DensityDescriptor(value) # somehow neccesarry
        return Density(Reference(
            reference="rhombus:generated/" + uuid_hash(value.as_dict()),
            default=value.AST)
        )
    
    @classmethod
    def referenced(cls, identifier: str) -> Density[Reference]:
        """Creates a Density refering to an externally provided density function."""
        return cls(Reference(identifier))
    

    #======// Toolchain //=======================================================================//

    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def from_datapack(cls, dp: beet.DataPack, identifier: str) -> Density | None:
        "⚠️ Currently experimental.<br>Creates a `Density` object from a density function in a Beet datapack."

        identifier = "minecraft:" + identifier if not ":" in identifier else identifier

        file = dp[beet_worldgen.WorldgenDensityFunction].get(identifier, default=None)
        if file is None:
            return None

        return Density.from_dict(file.data, dp=dp)
    
    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def from_dict(cls, d: JSONDict, /, dp: beet.DataPack | None = FROM_CONTEXT) -> Density:
        """Creates a `Density` object from a dictionary.
        
        A Beet datapack can be provided as context.
        """
        return Density(decode_HOLDER_HELPER_CODEC(d, dp=dp))
    
    def compile(self, with_identifier: str, /) -> dict[str, BeetFileClass]:
        "Compiles the Density into Beet file class instances."
        return compile(density=self.AST, identifier=with_identifier)

    def inject(self, dp: beet.DataPack, with_identifier: str) -> None:
        """Implements the Density and all additionally needed files in a Beet datapack.
        
        Parameters
        -------
        dp : DataPack
            The datapack the density function is to be implemented in.
        with_name : str
            A resource identifier under which the density function will be available.
        log : bool
            Whether to print the progress of the injection to the console.
        """

        files = self.compile(with_identifier)

        for id, file in files.items():
            dp[id] = file
            # print(f"Implemented {type(file).__name__} '{id}'")
            
        # print(f"Finished implementing density function '{with_identifier}'")
    
    def as_dict(self) -> JSONDict:
        """Only for debugging.<br>Returns the density function AST as a key-value-mapping like it can be used in a density function definition file.<br>
        The dictionary will not be fully inline. References that require separate files will be references."""
        return self.compile("a:a")["a:a"].data

    def show_in_dir(self, with_name: str = "test"):
        "Only for debugging.<br>Opens a temporary directory with all the compiled files. The directory will be deleted when pressing Enter in the console."
        from rhombus.core.compiler import show_in_temp
        files = self.compile(with_name)
        show_in_temp(files)
        
    
    #======// Arithmetic Magic //================================================================//
    
    def __add__(self, other) -> Density[types.add]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(types.add(self, other))
    
    def __radd__(self, other) -> Density[types.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[types.add]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(
            types.add(
                argument1=self,
                argument2=types.mul(
                    argument1=other,
                    argument2=constant(-1.0)
            )))
    
    def __rsub__(self, other) -> Density[types.add]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(
            types.add(
                argument1=other,
                argument2=types.mul(
                    argument1=self,
                    argument2=constant(-1.0)
            )))
    
    def __mul__(self, other) -> Density[types.mul]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(types.mul(self, other))
    
    def __rmul__(self, other) -> Density[types.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[types.mul]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(types.mul(self, types.invert(other)))
    
    def __rtruediv__(self, other) -> Density[types.mul]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(types.mul(other, types.invert(self)))
    
    @overload
    def __pow__(self, other: Literal[2]) -> Density[types.square]: ...
    @overload
    def __pow__(self, other: Literal[3]) -> Density[types.cube]: ...
    @overload
    def __pow__(self, other: int) -> Density[types.mul]: ...
    def __pow__(self, other):
        wrapped = self.AST
        if not isinstance(other, int):
            raise ValueError("Can't raise to non-integer powers")
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
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(types.max(self, other))
    
    def __or__(self, other):
        other = resolve_DensityDescriptor(other).AST
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

    def __gt__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __lt__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __ge__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __le__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __bool__(self): raise NotImplementedError


#======// Additional Density Types //============================================================//

def ref(identifier: str, /) -> Density[Reference]:
    "Creates a Density that is a reference to an externally provided density function."
    return Density.referenced(identifier)