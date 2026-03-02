from __future__ import annotations
from dataclasses import dataclass
from typing import Self, Callable, TypeAliasType, Union, Literal, overload, get_args, get_origin
from types import UnionType
from Rhombus import config
from Rhombus.core.density_function import DensityFunction, constant, Reference
from Rhombus.core.utils import JSONDict, Decorator, uuid_hash, contextfunction, FROM_CONTEXT
from Rhombus.core.codec import decode_HOLDER_HELPER_CODEC
from Rhombus.language import dft as dft
import beet, beet.contrib.worldgen as beet_worldgen
import inspect, functools

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
        result = dft.mul(next(it), next(it))
        for x in it:
            result = dft.mul(result, x)

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
    """A helper decorator for macros, that take (among other) density function inputs.

    The following effects are applied:
    - Function arguments annotated with `DensityDescriptor` are canonicalized (see the `unwrap` parameter)
    - Literal constant values that are larger than accepted are split into multiplications

    Parameters
    -------
    unwrap : bool
        Whether to pass the resolved `DensityDescriptor` arguments of the function as `DensityFunctionType` objects instead of `Density` objects
    """
    
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
    
    Don't use the constructor of this class. To define a new density instead use:<br>
    - Methods from `Rhombus.language.builtins` or other methods that return a `Density` for calculations
    - `.configured()` if a value is needed that can be easily altered in the compiled datapack later
    - `.separated()` if a density function has to be compiled to a separate file, but it is not important what this file is
    - `.referenced()` to reference a density function that is provided externally, like by another datapack
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
    @BuiltinWizard
    def configured(cls, name: str, default: DensityDescriptor) -> Density[Reference]:
        """Creates a Density that will be casted into a specific file when compiling."""
        name = "minecraft:" + name if not ":" in name else name
        if isinstance(default, Reference):
            default = dft.add(default, 0)
        return Density(Reference(name, default))
    
    @classmethod
    @BuiltinWizard
    def separated(cls, value: DensityDescriptor):
        """Creates a Density whose value will be casted into a separate file when compiling."""
        return Density(Reference(
            reference="rhombus:generated/" + uuid_hash(Density(value).as_dict()),
            default=value)
        )
    
    @classmethod
    def referenced(identifier: str) -> Density[Reference]:
        """Creates a Density refering to an externally provided density function."""
        return Density(Reference(identifier))


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
    
    def compile(self, with_identifier: str, /):
        "Compiles the Density into Beet file class instances."
        from Rhombus import toolchain
        return toolchain.compile(density=self, identifier=with_identifier)

    def inject(self, dp: beet.DataPack, with_identifier: str, /, log: bool = True) -> None:
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
            if log: print(f"Implemented {type(file).__name__} '{id}'")
            
        if log: print(f"Finished implementing density function '{with_identifier}'")
    
    def as_dict(self) -> JSONDict:
        """Only for debugging.<br>Returns the density function AST as a key-value-mapping like it can be used in a density function definition file.<br>
        The dictionary will not be fully inline. References that require separate files will be references."""
        return self.compile("a:a")["a:a"].data

    def show_in_dir(self, with_name: str = "test"):
        "Only for debugging.<br>Opens a temporary directory with all the compiled files. The directory will be deleted when pressing Enter in the console."
        from Rhombus import toolchain
        files = self.compile(with_name)
        toolchain.show_in_temp(files)
        
    
    #======// Arithmetic Magic //================================================================//
    
    def __add__(self, other) -> Density[dft.add]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(dft.add(self, other))
    
    def __radd__(self, other) -> Density[dft.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[dft.add]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(
            dft.add(
                argument1=self,
                argument2=dft.mul(
                    argument1=other,
                    argument2=constant(-1.0)
            )))
    
    def __rsub__(self, other) -> Density[dft.add]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(
            dft.add(
                argument1=other,
                argument2=dft.mul(
                    argument1=self,
                    argument2=constant(-1.0)
            )))
    
    def __mul__(self, other) -> Density[dft.mul]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(dft.mul(self, other))
    
    def __rmul__(self, other) -> Density[dft.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[dft.mul]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(dft.mul(self, dft.invert(other)))
    
    def __rtruediv__(self, other) -> Density[dft.mul]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(dft.mul(other, dft.invert(self)))
    
    @overload
    def __pow__(self, other: Literal[2]) -> Density[dft.square]: ...
    @overload
    def __pow__(self, other: Literal[3]) -> Density[dft.cube]: ...
    @overload
    def __pow__(self, other: int) -> Density[dft.mul]: ...
    def __pow__(self, other):
        wrapped = self.AST
        if not isinstance(other, int):
            raise ValueError("Can't raise to non-integer powers")
        if other == 0:
            return Density(dft.constant(1))
        elif other == 1:
            return self
        elif other == 2:
            return Density(dft.square(wrapped))
        elif other == 3:
            return Density(dft.cube(wrapped))
        elif other > 3:
            s = Density(dft.mul(wrapped, wrapped))
            for i in range(other - 2):
                s = Density(dft.mul(s.AST, wrapped))
            return s

    def __and__(self, other):
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(dft.max(self, other))
    
    def __or__(self, other):
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(dft.min(self, other))
    
    def __abs__(self) -> "Density[dft.abs]":
        return Density(dft.abs(self.AST))
    
    def __neg__(self) -> Density[dft.mul]:
        return Density(dft.mul(self.AST, constant(-1.0)))
    
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