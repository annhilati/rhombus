from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic, Self, overload, Tuple
from rhombus.core import df_types as dft, DFType


#======// Helpers //=============================================================================//

@overload
def _arg_unwrapper(args: Density | float | str) -> dft.DensityFunctionTypeBase: ...
def _arg_unwrapper(*args: Density | float | str) -> Tuple[dft.DensityFunctionTypeBase]:
    "Replaces strings with density function references and numbers with constant densities in a list of arguments."
    out = []
    for arg in args:
        if isinstance(arg, Density):
            out.append(arg.wrapped)
            continue
        elif isinstance(arg, str):
            out.append(dft.Reference(arg))
            continue
        elif isinstance(arg, (int, float)):
            out.append(dft.constant(float(arg)))
            continue
        out.append(arg)
    return out[0] if len(out) <= 1 else tuple(out)


#======// Density Type //========================================================================//

@dataclass
class Density(Generic[DFType]):
    """Class representing a density calculation."""

    wrapped: DFType

    def __repr__(self) -> str:
        return self.wrapped.__repr__()
    
    def TEMP(self) -> dict[str, Any]:
        return self.wrapped.encode()
    
    #======// Arithmetic Magic //====================================================================//
    
    def __add__(self, other) -> Density[dft.add]:
        self, other = _arg_unwrapper(self, other)
        return Density(dft.add(self, other))
    
    def __radd__(self, other) -> Density[dft.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[dft.add]:
        self, other = _arg_unwrapper(self, other)
        return Density(
            dft.add(
                argument1=self,
                argument2=dft.mul(
                    argument1=other,
                    argument2=dft.constant(-1)
            )))
    
    def __rsub__(self, other) -> Density[dft.add]:
        self, other = _arg_unwrapper(self, other)
        return Density(
            dft.add(
                argument1=other,
                argument2=dft.mul(
                    argument1=self,
                    argument2=dft.constant(-1)
            )))
    
    def __mul__(self, other) -> Density[dft.mul]:
        self, other = _arg_unwrapper(self, other)
        return Density(dft.mul(self, other))
    
    def __rmul__(self, other) -> Density[dft.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[dft.mul]:
        self, other = _arg_unwrapper(self, other)
        return Density(dft.mul(
            self,
            dft.invert(other)
        ))
    
    def __rtruediv__(self, other) -> Density[dft.mul]:
        self, other = _arg_unwrapper(self, other)
        return Density(dft.mul(
            other,
            dft.invert(self)
        ))
    
    def __pow__(self, other) -> Density[dft.square | dft.cube | dft.mul]:
        self = _arg_unwrapper(self)
        if not isinstance(other, int):
            raise ValueError("Can't raise to non integer powers")
        if other == 0:
            return 1
        elif other == 1:
            return self
        elif other == 2:
            return Density(dft.square(self))
        elif other == 3:
            return Density(dft.cube(self))
        elif other > 3:
            s = Density(dft.mul(self, self))
            for i in range(other - 2):
                s = Density(dft.mul(s.wrapped, self))
            return s
    
    def __abs__(self) -> Density[dft.abs]:
        return Density(dft.abs(self.wrapped))
    
    def __neg__(self) -> Density[dft.mul]:
        return Density(dft.mul(self.wrapped, dft.constant(-1)))
    
    def __pos__(self) -> Self:
        return self
    

    #======// Logical Magic //===================================================================//
    
    def __eq__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate makro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __ne__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate makro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __gt__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate makro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __lt__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate makro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __ge__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate makro or contribute to https://github.com/annhilati/rhombus/issues/4")
    def __le__(self, other): raise NotImplementedError("Densities are only symbolic values and can't be compared. For conditionality use 'range_choice' or an adequate makro or contribute to https://github.com/annhilati/rhombus/issues/4")
    

    #======// Shortcuts //=======================================================================//

    def cache_once(self) -> None:
        self.wrapped = dft.cache_once(self.wrapped)

    def interpolated(self) -> None:
        self.wrapped = dft.interpolated(self.wrapped)

    def cache_2d(self) -> None:
        self.wrapped = dft.cache_2d(self.wrapped)

    def flat_cache(self) -> None:
        self.wrapped = dft.flat_cache(self.wrapped)
    
def DensityReference(identifier: str, /) -> Density[dft.Reference]:
    return Density(dft.Reference(identifier))