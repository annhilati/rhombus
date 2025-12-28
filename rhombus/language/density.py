from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic
from rhombus.core import df_types as dft, DFType

#======// Helpers //=============================================================================//

def _interpret_args(*args: tuple[Density | float | str]) -> tuple[Density[Any | dft.Reference | dft.constant]]:
    "Replaces strings with density function references and numbers with constant densities in a list of arguments."
    out = []
    for arg in args:
        if isinstance(arg, str):
            out.append(Density(dft.Reference(arg)))
            continue
        if isinstance(arg, (int, float)):
            out.append(Density(dft.constant(float(arg))))
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
    
    def as_dict(self) -> dict[str, Any]:
        return self.wrapped.encode()
    
    #======// Arithmetic Magic //====================================================================//
    
    def __add__(self, other) -> Density[dft.add]:
        other = _interpret_args(other)
        return Density(dft.add(self.wrapped, other))
    
    def __radd__(self, other) -> Density[dft.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[dft.add]:
        other = _interpret_args(other)
        return Density(
            dft.add(
                argument1=self.wrapped,
                argument2=dft.mul(
                    argument1=other,
                    argument2=-1
            )))
    
    def __rsub__(self, other) -> Density[dft.add]:
        other = _interpret_args(other)
        return Density(
            dft.add(
                argument1=other,
                argument2=dft.mul(
                    argument1=self.wrapped,
                    argument2=-1
            )))
    
    def __mul__(self, other) -> Density[dft.mul]:
        other = _interpret_args(other)
        return Density(dft.mul(self.wrapped, other))
    
    def __rmul__(self, other) -> Density[dft.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[dft.mul]:
        other = _interpret_args(other)
        return Density(dft.mul(
            self.wrapped,
            dft.invert(other)
        ))
    
    def __rtruediv__(self, other) -> Density[dft.mul]:
        other = _interpret_args(other)
        return Density(dft.mul(
            other,
            dft.invert(self.wrapped)
        ))
    
    def __pow__(self, other) -> Density[dft.square | dft.cube | dft.mul]:
        if not isinstance(other, int):
            raise ValueError("Can't raise to non integer powers")
        if other == 0:
            return 1
        elif other == 1:
            return self
        elif other == 2:
            return Density(dft.square(self.wrapped))
        elif other == 3:
            return Density(dft.cube(self.wrapped))
        elif other > 3:
            s = Density(dft.mul(self.wrapped, self.wrapped))
            for i in range(other - 2):
                s = Density(dft.mul(s, self.wrapped))
            return s
    
    def __abs__(self) -> Density[dft.abs]:
        return Density(dft.abs(argument=self.wrapped))
    
    def __neg__(self) -> Density[dft.mul]:
        return Density(dft.mul(self.wrapped, dft.constant(-1)))
    
def DensityReference(identifier: str, /) -> Density[dft.Reference]:
    return Density(dft.Reference(identifier))

r = DensityReference