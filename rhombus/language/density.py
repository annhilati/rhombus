from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic, Self, TypeVar, TypeAlias, Union, Literal, overload
from rhombus.core import df_types as dft

WrappedDFType = TypeVar("WrappedFunctionType", bound=dft.DensityFunctionType, default=dft.DensityFunctionType)
"Type variable for all subclasses of `DensityFunctionTypeBase`."

DensityDescriptor: TypeAlias = Union["Density", dft.DensityFunctionType, str, float]

#======// Formatters //==========================================================================//

def resolve_shorthand(arg: DensityDescriptor) -> Density:
    if isinstance(arg, Density):
        return arg
    elif isinstance(arg, dft.DensityFunctionType):
        return Density(arg)
    elif isinstance(arg, str):
        if not ":" in arg: arg = "minecraft:" + arg
        return Density(dft.Reference(arg))
    elif isinstance(arg, (int, float)):
        return Density(dft.constant(float(arg)))
    raise ValueError(arg, type(arg))

def resolve_shorthands(*args: Density | dft.DensityFunctionType | float | str) -> tuple[Density, ...]:
    "Resolves all expressions to Densities that are possible."
    return tuple([resolve_shorthand(a) for a in args])

def unwrap_resolved(*args: Density | dft.DensityFunctionType | float | str) -> tuple[dft.DensityFunctionType, ...]:
    "Replaces strings with density function references and numbers with constant densities in a list of arguments."
    return tuple([resolve_shorthand(a).wrapped for a in args])

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
        return self.wrapped.encode()
    
    #======// Arithmetic Magic //================================================================//
    
    def __add__(self, other) -> Density[dft.add]:
        self, other = unwrap_resolved(self, other)
        return Density(dft.add(self, other))
    
    def __radd__(self, other) -> Density[dft.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[dft.add]:
        self, other = unwrap_resolved(self, other)
        return Density(
            dft.add(
                argument1=self,
                argument2=dft.mul(
                    argument1=other,
                    argument2=dft.constant(-1)
            )))
    
    def __rsub__(self, other) -> Density[dft.add]:
        self, other = unwrap_resolved(self, other)
        return Density(
            dft.add(
                argument1=other,
                argument2=dft.mul(
                    argument1=self,
                    argument2=dft.constant(-1)
            )))
    
    def __mul__(self, other) -> Density[dft.mul]:
        self, other = unwrap_resolved(self, other)
        return Density(dft.mul(self, other))
    
    def __rmul__(self, other) -> Density[dft.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[dft.mul]:
        self, other = unwrap_resolved(self, other)
        return Density(dft.mul(
            self,
            dft.invert(other)
        ))
    
    def __rtruediv__(self, other) -> Density[dft.mul]:
        self, other = unwrap_resolved(self, other)
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
        
    def __and__(self, other):
        self, other = unwrap_resolved(self, other)
        return Density(dft.max(self, other))
    
    def __or__(self, other):
        self, other = unwrap_resolved(self, other)
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

    def __new__(cls, name: str, default: DensityDescriptor) -> Density[dft.Reference]:
        wrapped = resolve_shorthand(default).wrapped
        if isinstance(wrapped, dft.Reference):
            wrapped = dft.add(wrapped, 0)
        return Density(dft.Reference(name, wrapped))

@dataclass(init=False)
class DensityReference:
    """
    
    `DensityReference(id)` is identical to `ref(id)`.
    """

    def __new__(identifier: str, /) -> Density[dft.Reference]:
        return ref(identifier)
    
def ref(identifier: str, /) -> Density[dft.Reference]:
    return Density(dft.Reference(identifier))