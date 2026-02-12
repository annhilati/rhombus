from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic, Self, Callable, TypeVar, TypeAlias, Union, Literal, ParamSpec, overload, get_args, get_origin
from Rhombus.core import df_types as dft, config
from Rhombus.core.utils import JSONDict, uuid_hash
import beet, beet.contrib.worldgen as beet_worldgen
import inspect, functools

__all__ = ["Density", "DensityDescriptor", "ConfiguredDensity", "DensityReference", "ExternalDensity", "ref", "MacroWizard", "BuiltinWizard",]

_decode_cache: dict[str, dft.DensityFunctionExpression] = {}

#======// Formatters //==========================================================================//

DensityDescriptor: TypeAlias = Union["Density", dft.DensityFunctionExpression, str, float]
"UnionType for all types that can be interpreted by `resolve_DensityDescriptor()`."

def resolve_DensityDescriptor(arg: DensityDescriptor) -> Density:
    """Interprets a QoL argument input and returns a Density object.
    Applies logic like splitting large literal constants into calculations
    before constructing constant AST nodes.
    """

    limit = config.constant_number_limit

    if isinstance(arg, (int, float)):
        v = float(arg)

        if abs(v) <= limit:
            return Density(dft.constant(v))

        sign = -1.0 if v < 0 else 1.0
        v = abs(v)

        factors: list[float] = []
        while v > limit:
            factors.append(float(limit))
            v /= limit

        factors.append(v * sign)

        it = iter(dft.constant(f) for f in factors)
        result = dft.mul(next(it), next(it))
        for x in it:
            result = dft.mul(result, x)

        return Density(result)

    if isinstance(arg, Density):
        return arg

    if isinstance(arg, dft.DensityFunctionExpression):
        return Density(arg)

    if isinstance(arg, str):
        if ":" not in arg:
            arg = "minecraft:" + arg
        return Density(dft.Reference(arg))

    raise ValueError(f"Cannot resolve type {type(arg)} to a density function")

def _is_density_descriptor(annotation) -> bool:
    if annotation is None:
        return False
    if annotation is DensityDescriptor:
        return True
    origin = get_origin(annotation)
    return origin is DensityDescriptor or (
        origin is not None and DensityDescriptor in get_args(annotation)
    )

_P = ParamSpec("Params")
_R = TypeVar("Result")

def MacroWizard(fn: Callable[_P, _R] = None, *, unwrap: bool = False):
    """A helper decorator for macros, that take (among other) density function inputs.

    The following effects are applied:
    - Function arguments annotated with `DensityDescriptor` are canonicalized (see the `unwrap` parameter)
    - Literal constant values that are larger than accepted are split into multiplications

    Parameters
    -------
    unwrap : bool
        Whether to pass the resolved `DensityDescriptor` arguments of the function as `DensityFunctionType` objects instead of `Density` objects
    """

    def _to_ast(obj: Any) -> Any:
        try:
            DensityType = globals().get("Density")
        except Exception:
            DensityType = None

        if DensityType is not None and isinstance(obj, DensityType):
            return obj.AST

        wrapped = getattr(obj, "wrapped", obj)
        if DensityType is not None and isinstance(wrapped, DensityType):
            return wrapped.AST

        return wrapped

    def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
        sig = inspect.signature(func)
        
        params_to_resolve = {
            name for name, param in sig.parameters.items()
            if _is_density_descriptor(param.annotation)
        }

        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for name in params_to_resolve:
                if name in bound.arguments:
                    current_val = bound.arguments[name]
                    resolved = resolve_DensityDescriptor(current_val)

                    if unwrap:
                        bound.arguments[name] = _to_ast(resolved)
                    else:
                        bound.arguments[name] = resolved

            return func(*bound.args, **bound.kwargs)

        wrapper.__signature__ = sig
        return wrapper

    if fn is not None:
        return decorator(fn)

    return decorator

def BuiltinWizard(fn: Callable[_P, _R]) -> Callable[_P, _R]:
    "Shortcut for `MacroWizard(unwrap=True)`"
    return MacroWizard(unwrap=True)(fn)


#======// Density Type //========================================================================//

WrappedDFType = TypeVar("DensityFunctionType", bound=dft.DensityFunctionExpression, default=dft.DensityFunctionExpression)

@dataclass
class Density(Generic[WrappedDFType]):
    """Class representing a density calculation.
    
    Don't use the constructor of this class. To define a new density instead use:<br>
    - Methods from `Rhombus.language.builtins` or other methods that return a `Density` for calculations
    - `ConfiguredDensity` if a value is needed that can be easily altered in the compiled datapack later
    - `ExternalDensity` if a density function has to be compiled to a separate file, but it is not important what this file is
    - `DensityReference` to reference a density function that is provided externally, like by another datapack
    """

    AST: WrappedDFType
    "The density function AST represented by this Density."

    def __post_init__(self):
        if isinstance(self.AST, Density):
            raise Exception("A Density object was initialized, with another Density object as its contents")

    def __repr__(self) -> str:
        return self.AST.__repr__()
    
    @property
    def cc(self) -> int:
        "Returns the **compilation complexity** of the density function AST."
        return self.AST.compilation_complexity
    

    #======// Toolchain //=======================================================================//

    @classmethod
    def from_datapack(cls, dp: beet.DataPack, identifier: str) -> Density | None:
        "⚠️ Currently experimental.<br>Creates a `Density` object from a density function in a Beet datapack."
        from Rhombus.core.df_types import decode_HOLDER_HELPER_CODEC

        identifier = "minecraft:" + identifier if not ":" in identifier else identifier

        file = dp[beet_worldgen.WorldgenDensityFunction][identifier]
        if file is None:
            return None
        data = file.data

        return Density(decode_HOLDER_HELPER_CODEC(data, dp=dp))
    
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
        toolchain.summon(files)
        
    
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
                    argument2=dft.constant(-1.0)
            )))
    
    def __rsub__(self, other) -> Density[dft.add]:
        other = resolve_DensityDescriptor(other).AST
        self = self.AST
        return Density(
            dft.add(
                argument1=other,
                argument2=dft.mul(
                    argument1=self,
                    argument2=dft.constant(-1.0)
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
            return 1
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
    
    def __abs__(self) -> Density[dft.abs]:
        return Density(dft.abs(self.AST))
    
    def __neg__(self) -> Density[dft.mul]:
        return Density(dft.mul(self.AST, dft.constant(-1.0)))
    
    def __pos__(self) -> Self:
        return self
    

    #======// Logical Magic //===================================================================//
    
    def __eq__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __ne__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __gt__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __lt__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __ge__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __le__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate macro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __bool__(self): raise NotImplementedError


#======// Additional Density Types //============================================================//

def ref(identifier: str, /) -> Density[dft.Reference]:
    "Creates a Density that is a reference to an externally provided density function."
    return resolve_DensityDescriptor(identifier)


@dataclass(init=False)
class ConfiguredDensity:
    """Creates a Density that will be casted into a specific file when compiling."""

    @BuiltinWizard
    def __new__(cls, name: str, default: DensityDescriptor) -> Density[dft.Reference]:
        default = resolve_DensityDescriptor(default).AST # This somehow is neccesarry
        if isinstance(default, dft.Reference):
            default = dft.add(default, 0)
        return Density(dft.Reference(name, default))


@dataclass(init=False)
class ExternalDensity:
    """Creates a Density whose value will be casted into a separate file when compiling."""

    @BuiltinWizard
    def __new__(cls, value: DensityDescriptor, /):
        return Density(dft.Reference(
            reference="rhombus:generated/" + uuid_hash(Density(value).as_dict()),
            default=value)
        )


@dataclass(init=False)
class DensityReference:
    """Creates a Density refering to an externally provided density function."""

    def __new__(cls, identifier: str, /) -> Density[dft.Reference]:
        return ref(identifier)