from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, Type
from density.core import density_function_types as dft

T = TypeVar("T", bound=dft.DensityFunctionTypeBase)

# things to respect when building the JSON
# - Don't create multiple equivalent noises and use references
# - Respect caching functions and split into multiples and use references

@dataclass
class Density(Generic[T]):
    """Class representing a density function tree."""

    type:       Type[T]
    parameters: dict[str, Any]

    def __init__(self, type: Type[T], **parameters):
        self.type = type
        self.parameters = parameters

    def __repr__(self) -> str:
        return f"{self.type.__name__}({", ".join([f'{key}={value}' for key, value in self.parameters.items()])})"
    
    def as_density_function(self) -> dict[str, Any]:
        return self.type.as_density_function(self.parameters)
    
    #======// Arithmetic Magic //====================================================================//
    
    def __add__(self, other) -> Density[dft.add]:
        return Density(dft.add, argument1=self, argument2=other)
    
    def __radd__(self, other) -> Density[dft.add]:
        return self.__add__(other)
    
    def __sub__(self, other) -> Density[dft.add]:
        return Density(
            dft.add,
            argument1=self,
            argument2=Density(
                dft.mul,
                argument1=other,
                argument2=-1
            )
            )
    
    def __rsub__(self, other) -> Density[dft.add]:
        return Density(
            dft.add,
            argument1=other,
            argument2=Density(
                dft.mul,
                argument1=self,
                argument2=-1,
                )
            )
    
    def __mul__(self, other) -> Density[dft.mul]:
        return Density(dft.mul, argument1=self, argument2=other)
    
    def __rmul__(self, other) -> Density[dft.mul]:
        return self.__mul__(other)
    
    def __truediv__(self, other) -> Density[dft.mul]:
        return Density(
            dft.mul,
            argument1=self,
            argument2=Density(dft.invert, argument=other)
        )
    
    def __rtruediv__(self, other) -> Density[dft.mul]:
        return Density(
            dft.mul,
            argument1=other,
            argument2=Density(dft.invert, argument=self)
        )
    
    def __pow__(self, other) -> Density[dft.square | dft.cube | dft.mul]:
        if type(other) is not int:
            raise ValueError("Can't raise to non integer powers")
        if other == 0:
            return Density(dft.constant, argument=1)
        elif other == 1:
            return self
        elif other == 2:
            return Density(dft.square, argument=self)
        elif other == 3:
            return Density(dft.cube, argument=self)
        elif other > 3:
            s = Density(dft.mul, argument1=self, argument2=self)
            for i in range(other - 2):
                s = Density(dft.mul, argument1=s, argument2=self)
            return s
    
    def __abs__(self) -> Density[dft.abs]:
        return Density(dft.abs, argument=self)