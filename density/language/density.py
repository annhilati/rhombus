from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic, TypeVar
from density.core import df_types as dft, DFType

@dataclass
class Density(Generic[DFType]):
    """Class representing a density calculation."""

    function: DFType

    def __repr__(self) -> str:
        return self.function.__repr__()
    
    def as_dict(self) -> dict[str, Any]:
        return self.function.encode()
    
    #======// Arithmetic Magic //====================================================================//
    
    def __add__(self, other) -> Density[dft.add]:
        if isinstance(other, Density):
            other = other.function
        return Density(dft.add(self.function, other))
    
    def __radd__(self, other) -> Density[dft.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[dft.add]:
        if isinstance(other, Density):
            other = other.function
        return Density(
            dft.add(
                argument1=self.function,
                argument2=dft.mul(
                    argument1=other,
                    argument2=-1
            )))
    
    def __rsub__(self, other) -> Density[dft.add]:
        if isinstance(other, Density):
            other = other.function
        return Density(
            dft.add(
                argument1=other,
                argument2=dft.mul(
                    argument1=self.function,
                    argument2=-1
            )))
    
    def __mul__(self, other) -> Density[dft.mul]:
        if isinstance(other, Density):
            other = other.function
        return Density(dft.mul(self.function, other))
    
    def __rmul__(self, other) -> Density[dft.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[dft.mul]:
        if isinstance(other, Density):
            other = other.function
        return Density(dft.mul(
            self.function,
            dft.invert(other)
        ))
    
    def __rtruediv__(self, other) -> Density[dft.mul]:
        if isinstance(other, Density):
            other = other.function
        return Density(dft.mul(
            other,
            dft.invert(self.function)
        ))
    
    def __pow__(self, other) -> Density[dft.square | dft.cube | dft.mul]:
        if not isinstance(other, int):
            raise ValueError("Can't raise to non integer powers")
        if other == 0:
            return 1
        elif other == 1:
            return self
        elif other == 2:
            return Density(dft.square(self.function))
        elif other == 3:
            return Density(dft.cube(self.function))
        elif other > 3:
            s = Density(dft.mul(self.function, self.function))
            for i in range(other - 2):
                s = Density(dft.mul(s, self.function))
            return s
    
    def __abs__(self) -> Density[dft.abs]:
        return Density(dft.abs(argument=self.function))
    
def DensityReference(identifier: str, /) -> Density[dft.Reference]:
    return Density(dft.Reference(identifier))