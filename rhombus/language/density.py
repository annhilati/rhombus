from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic, Self, TypeVar, TypeAlias, Union, Literal, overload
from rhombus.core import df_types as dft
from rhombus.core import config

WrappedDFType = TypeVar("WrappedFunctionType", bound=dft.DensityFunctionType, default=dft.DensityFunctionType)
"Type variable for all subclasses of `DensityFunctionTypeBase`."

DensityDescriptor: TypeAlias = Union["Density", dft.DensityFunctionType, str, float]

#======// Formatters //==========================================================================//

def resolve_DensityDescriptor(arg: DensityDescriptor) -> Density:
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
    if isinstance(out.wrapped, dft.constant) and (v := out.wrapped.argument) > limit:

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
        out.wrapped.argument = result
    return out

from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

def resolve_inputs(*, unwrap: bool = False):
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        import inspect
        from functools import wraps
        from typing import get_origin, get_args

        def _is_density_descriptor(annotation) -> bool:
            if annotation is DensityDescriptor:
                return True
            origin = get_origin(annotation)
            return origin is DensityDescriptor or (
                origin is not None and DensityDescriptor in get_args(annotation)
            )

        sig = inspect.signature(fn)
        params = {
            name for name, param in sig.parameters.items()
            if _is_density_descriptor(param.annotation)
        }

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for name in params:
                if name in bound.arguments:
                    value = resolve_DensityDescriptor(bound.arguments[name])
                    bound.arguments[name] = value.wrapped if unwrap else value

            return fn(*bound.args, **bound.kwargs)

        wrapper.__signature__ = sig
        return wrapper

    return decorator



def resolve_and_unwrap_inputs(fn):
    "Use this dec"
    from functools import wraps
    decorated = resolve_inputs(fn, unwrap=True)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        return decorated(*args, **kwargs)

    wrapper.__signature__ = getattr(decorated, "__signature__", None)
    return wrapper


#======// Density Type //========================================================================//

@dataclass
class Density(Generic[WrappedDFType]):
    """Class representing a density calculation.
    
    Don't use the constructor of this class. Use `rhombus.constant()` or any methods in `rhombus.language.builtins` instead.
    """

    wrapped: WrappedDFType

    def __repr__(self) -> str:
        return self.wrapped.__repr__()
    
    def as_dict(self) -> dict[str, Any]:
        "Returns the density function AST as a key-value-mapping like it can be used in a density function definition file."
        return self.wrapped.encode()
    
    @property
    def cc(self) -> int:
        "Returns the compilation complexity of the density function AST."
        return self.wrapped.compilation_complexity
    
    #======// Arithmetic Magic //================================================================//
    
    @resolve_and_unwrap_inputs
    def __add__(self, other) -> Density[dft.add]:
        return Density(dft.add(self, other))
    
    def __radd__(self, other) -> Density[dft.add]:
        return self.__add__(other)
    
    @resolve_and_unwrap_inputs
    def __sub__(self, other) -> Density[dft.add]:
        return Density(
            dft.add(
                argument1=self,
                argument2=dft.mul(
                    argument1=other,
                    argument2=dft.constant(-1)
            )))
    
    @resolve_and_unwrap_inputs
    def __rsub__(self, other) -> Density[dft.add]:
        return Density(
            dft.add(
                argument1=other,
                argument2=dft.mul(
                    argument1=self,
                    argument2=dft.constant(-1)
            )))
    
    @resolve_and_unwrap_inputs
    def __mul__(self, other) -> Density[dft.mul]:
        return Density(dft.mul(self, other))
    
    def __rmul__(self, other) -> Density[dft.mul]:
        return self.__mul__(other)
    
    @resolve_and_unwrap_inputs
    def __truediv__(self, other) -> Density[dft.mul]:
        return Density(dft.mul(
            self,
            dft.invert(other)
        ))
    
    @resolve_and_unwrap_inputs
    def __rtruediv__(self, other) -> Density[dft.mul]:
        return Density(dft.mul(
            other,
            dft.invert(self)
        ))
    
    @overload
    def __pow__(self, other: Literal[2]) -> Density[dft.square]: ...
    @overload
    def __pow__(self, other: Literal[3]) -> Density[dft.cube]: ...
    @overload
    def __pow__(self, other: int) -> Density[dft.mul]: ...
    def __pow__(self, other):
        wrapped = self.wrapped
        if not isinstance(other, int):
            raise ValueError("Can't raise to non integer powers")
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
                s = Density(dft.mul(s.wrapped, wrapped))
            return s

    @resolve_and_unwrap_inputs    
    def __and__(self, other):
        return Density(dft.max(self, other))
    
    @resolve_and_unwrap_inputs
    def __or__(self, other):
        return Density(dft.min(self, other))
    
    def __abs__(self) -> Density[dft.abs]:
        return Density(dft.abs(self.wrapped))
    
    def __neg__(self) -> Density[dft.mul]:
        return Density(dft.mul(self.wrapped, dft.constant(-1)))
    
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

    def cache_once(self) -> None:
        self.wrapped = dft.cache_once(self.wrapped)

    def interpolated(self) -> None:
        self.wrapped = dft.interpolated(self.wrapped)

    def cache_2d(self) -> None:
        self.wrapped = dft.cache_2d(self.wrapped)

    def flat_cache(self) -> None:
        self.wrapped = dft.flat_cache(self.wrapped)


#======// Additional Density Types //============================================================//

@dataclass(init=False)
class ConfiguredDensity:
    """Defines an external density functions, that comes with a default value on compilation.
    """

    @resolve_and_unwrap_inputs
    def __new__(cls, name: str, default: DensityDescriptor) -> Density[dft.Reference]:
        if isinstance(default, dft.Reference):
            default = dft.add(default, 0)
        return Density(dft.Reference(name, default))

@dataclass(init=False)
class DensityReference:
    """
    
    `DensityReference(id)` is identical to `ref(id)`.
    """

    def __new__(identifier: str, /) -> Density[dft.Reference]:
        return ref(identifier)
    
def ref(identifier: str, /) -> Density[dft.Reference]:
    return Density(dft.Reference(identifier))