# Datapack version 113 was introduced with 26.3-snap6

from rhombus.std.density import Density
from rhombus.std.types import types

def pow(base: Density, exponent: int) -> Density[types.square | types.cube | types.mul | types.invert]:
    wrapped = base.AST
    if not isinstance(exponent, int):
        raise ValueError("Can only raise to integer powers in this version")
    if exponent == 0:
        return Density(types.constant(1))
    elif exponent == 1:
        return base
    elif exponent == 2:
        return Density(types.square(wrapped))
    elif exponent == 3:
        return Density(types.cube(wrapped))
    
    result = base
    for _ in range(abs(exponent) - 1):
        result = Density(types.mul(result.AST, wrapped))
    if exponent < 0:
        result = Density(types.invert(result.AST))
    return result