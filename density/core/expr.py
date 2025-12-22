from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Generic, TypeVar, Type
from density.core import density_function_types as dft

T = TypeVar("T", bound=dft.DensityFunctionTypeBase)

# things to respect when building the JSON
# - Don't create multiple equivalent noises and use references
# - Respect caching functions and split into multiples and use references

@dataclass
class Density(Generic[T]):
    """Class representing a density function tree."""

    content: T

    def __repr__(self) -> str:
        return self.content.__repr__()
    
    def as_density_function(self) -> dict[str, Any]:
        return self.content.as_density_function()
    
    #======// Arithmetic Magic //====================================================================//
    
    def __add__(self, other) -> Density[dft.add]:
        if isinstance(other, Density):
            other = other.content
        return Density(dft.add(self.content, other))
    
    def __radd__(self, other) -> Density[dft.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[dft.add]:
        if isinstance(other, Density):
            other = other.content
        return Density(
            dft.add(
                argument1=self.content,
                argument2=dft.mul(
                    argument1=other,
                    argument2=-1
            )))
    
    def __rsub__(self, other) -> Density[dft.add]:
        if isinstance(other, Density):
            other = other.content
        return Density(
            dft.add(
                argument1=other,
                argument2=dft.mul(
                    argument1=self.content,
                    argument2=-1
            )))
    
    def __mul__(self, other) -> Density[dft.mul]:
        if isinstance(other, Density):
            other = other.content
        return Density(dft.mul(self.content, other))
    
    def __rmul__(self, other) -> Density[dft.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[dft.mul]:
        if isinstance(other, Density):
            other = other.content
        return Density(dft.mul,
            argument1=self.content,
            argument2=dft.invert(other)
        )
    
    def __rtruediv__(self, other) -> Density[dft.mul]:
        if isinstance(other, Density):
            other = other.content
        return Density(dft.mul,
            argument1=other,
            argument2=dft.invert(self.content)
        )
    
    def __pow__(self, other) -> Density[dft.square | dft.cube | dft.mul]:
        if not isinstance(other, int):
            raise ValueError("Can't raise to non integer powers")
        if other == 0:
            return 1
        elif other == 1:
            return self
        elif other == 2:
            return Density(dft.square(self.content))
        elif other == 3:
            return Density(dft.cube(self.content))
        elif other > 3:
            s = Density(dft.mul(self.content, self.content))
            for i in range(other - 2):
                s = Density(dft.mul(s, self.content))
            return s
    
    def __abs__(self) -> Density[dft.abs]:
        return Density(dft.abs(argument=self.content))
    
def DensityReference(identifier: str, /) -> Density[dft.Reference]:
    return Density(dft.Reference(identifier))