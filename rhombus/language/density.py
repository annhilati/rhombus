from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic, Self, Callable, TypeVar, TypeAlias, Union, Literal, ParamSpec, overload, get_args, get_origin
from rhombus.core import df_types as dft, config
from beet import Context

#======// Formatters //==========================================================================//

DensityDescriptor: TypeAlias = Union["Density", dft.DensityFunctionType, str, float]
"UnionType for all types that can be interpreted by `resolve_DensityDescriptor()`."

def resolve_DensityDescriptor(arg: DensityDescriptor) -> Density:
    """Interprets a QoL argument input and returns a Density object. Additionally applies logic like splitting large literal constants into calculations."""
    if isinstance(arg, Density):
        out = arg
    elif isinstance(arg, dft.DensityFunctionType):
        out = Density(arg)
    elif isinstance(arg, str):
        if not ":" in arg: arg = "minecraft:" + arg
        out = Density(dft.Reference(arg))
    elif isinstance(arg, (int, float)):
        out = Density(dft.constant(float(arg)))
    else:
        raise ValueError(arg, type(arg))
    
    limit = config.constant_number_limit
    if isinstance(out.AST, dft.constant) and (v := out.AST.argument) > limit:

        if v == 0: return out

        factors: list[float] = []
        v = abs(v)

        while v > limit:
            factors.append(float(limit))
            v /= limit

        factors.append(float(v * (-1.0 if v < 0 else 1.0)))
        
        it = iter([Density(dft.constant(f)) for f in factors])
        result = next(it) * next(it)

        for x in it:
            result = result * x
        out.AST.argument = result
    return out

def _is_density_descriptor(annotation) -> bool:
    if annotation is None:
        return False
    if annotation is DensityDescriptor:
        return True
    origin = get_origin(annotation)
    return origin is DensityDescriptor or (
        origin is not None and DensityDescriptor in get_args(annotation)
    )

P = ParamSpec("P")
R = TypeVar("R")

def resolve_inputs(fn: Callable[P, R] = None, *, unwrap: bool = False):
    import inspect, functools

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)
        
        params_to_resolve = {
            name for name, param in sig.parameters.items()
            if _is_density_descriptor(param.annotation)
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
                        bound.arguments[name] = getattr(resolved, "wrapped", resolved)
                    else:
                        bound.arguments[name] = resolved

            return func(*bound.args, **bound.kwargs)

        wrapper.__signature__ = sig
        return wrapper

    if fn is not None:
        return decorator(fn)

    return decorator

def resolve_and_unwrap_inputs(fn: Callable[P, R]) -> Callable[P, R]:
    return resolve_inputs(unwrap=True)(fn)


#======// Density Type //========================================================================//

WrappedDFType = TypeVar("WrappedFunctionType", bound=dft.DensityFunctionType, default=dft.DensityFunctionType)

@dataclass
class Density(Generic[WrappedDFType]):
    """Class representing a density calculation.
    
    Don't use the constructor of this class. To define a new density instead use:<br>
    - Methods from `rhombus.language.builtins` or other methods that return a `Density` for calculations
    - `ConfiguredDensity` if a value is needed that can be easily altered in the compiled datapack later
    - `ExternalDensity` if a density function has to be compiled to a separate file, but it is not important what this file is
    - `DensityReference` to reference a density function that is provided externally, like by another datapack
    """

    AST: WrappedDFType
    "The density function AST represented by this Density."

    def __repr__(self) -> str:
        return self.AST.__repr__()
    
    def as_dict(self) -> dict[str, Any]:
        "Returns the density function AST as a key-value-mapping like it can be used in a density function definition file."
        return self.AST.encode()
    
    @property
    def cc(self) -> int:
        "Returns the **compilation complexity** of the density function AST."
        return self.AST.compilation_complexity
    

    #======// Toolchain //=======================================================================//
    

    def compile(self, with_name: str, /):
        "Compiles the Density into Beet file class instances."
        from rhombus import toolchain
        return toolchain.compile(density=self, identifier=with_name)

    def inject(self, ctx: Context, with_name: str, /, log: bool = True) -> None:
        "Implements the Density and all additionally needed files in a Beet datapack."
        data = ctx.data

        files = self.compile(with_name)

        for id, file in files.items():
            data[id] = file
            if log: print(f"Implemented {type(file).__name__} '{id}'")
            
        if log: print(f"Finished implementing density function '{with_name}'")

    def show_in_dir(self, with_name: str = "test"):
        "Only for debugging.<br>Opens a temporary directory with all the compiled files. The directory will be deleted when pressing Enter in the console."
        from rhombus import toolchain
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
    

    #======// Shortcuts //=======================================================================//

    # def cache_once(self) -> None:
    #     self.wrapped = dft.cache_once(self.wrapped)

    # def interpolated(self) -> None:
    #     self.wrapped = dft.interpolated(self.wrapped)

    # def cache_2d(self) -> None:
    #     self.wrapped = dft.cache_2d(self.wrapped)

    # def flat_cache(self) -> None:
    #     self.wrapped = dft.flat_cache(self.wrapped)


#======// Additional Density Types //============================================================//

def ref(identifier: str, /) -> Density[dft.Reference]:
    return Density(dft.Reference(identifier))


@dataclass(init=False)
class ConfiguredDensity:
    """Creates a Density that will be casted into a specific file when compiling."""

    @resolve_and_unwrap_inputs
    def __new__(cls, name: str, default: DensityDescriptor) -> Density[dft.Reference]:
        default = resolve_DensityDescriptor(default).AST # This somehow is neccesarry
        if isinstance(default, dft.Reference):
            default = dft.add(default, 0)
        return Density(dft.Reference(name, default))


@dataclass(init=False)
class ExternalDensity:
    """Creates a Density whose value will be casted into a separate file when compiling."""

    @staticmethod
    def get_dictionary_uuid(data: dict[str, Any]) -> str:
        """Creates a UUID string (no `-`) based of a JSON dictionary."""
        import hashlib, uuid, json

        encoded_str = json.dumps(
            data, 
            sort_keys=True, 
            ensure_ascii=True, 
            separators=(',', ':')
        ).encode('utf-8')
        hash_digest = hashlib.sha256(encoded_str).digest()
        return str(uuid.UUID(bytes=hash_digest[:16])).replace("-", "")

    @resolve_and_unwrap_inputs
    def __new__(cls, value: DensityDescriptor, /):
        return Density(dft.Reference("rhombus:generated/" + ExternalDensity.get_dictionary_uuid(Density(value).as_dict()), value))


@dataclass(init=False)
class DensityReference:
    """Creates a Density refering to an externally provided density function."""

    def __new__(cls, identifier: str, /) -> Density[dft.Reference]:
        return ref(identifier)