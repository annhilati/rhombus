# Datapack version 113 was introduced with 26.3-snap6

from rhombus.std import Density
from rhombus.support import vanilla as vt

def pow(base: Density, exponent: int) -> Density[vt.square | vt.cube | vt.mul | vt.invert]:
    wrapped = base.AST
    if not isinstance(exponent, int):
        raise ValueError("Can only raise to integer powers in this version")
    if exponent == 0:
        return Density(vt.constant(1))
    elif exponent == 1:
        return base
    elif exponent == 2:
        return Density(vt.square(wrapped))
    elif exponent == 3:
        return Density(vt.cube(wrapped))
    
    result = base
    for _ in range(abs(exponent) - 1):
        result = Density(vt.mul(result.AST, wrapped))
    if exponent < 0:
        result = Density(vt.invert(result.AST))
    return result