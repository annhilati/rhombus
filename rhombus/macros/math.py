"""Macro module for general mathematical functions and constants."""

import math as py_math
from rhombus.std import Density, AnyDensity, f, types, macro
from rhombus.macros import conditional as cond, performance as perf

__all__ = [
    "Infinity", "NaN",
    "pi", "e",
    "sum", "prod",
    "round", "floor", "ceil",
    "mod", "floordiv",
    "heaviside", "ramp", "sgn", "monus",
    "sqrt_linear_01", "sqrt_rational_01",
]

#======// Numeric Constants //===================================================================//

Infinity = Density.constant(1) / 0
"Density equivalent to Java's `Double.POSITIVE_INFINITY`"
NaN = Density.constant(0) / 0
"""Density equivalent to Java's `Double.NaN`

**NOTE** `NaN` will be casted to `0.0` thus it will be interpreted as air.
"""
# TODO research whether this casting happens on occurance or just at the end

pi = 3.1415926535897932 #38462643383279502884197169399375105820974944592307816406
"The constant `π` to 16 decimals."
e  = 2.7182818284590452 #35360287471352662497757247093699959574966
"Euler's number `e` to 16 decimals."


#======// Arithmetic //==========================================================================//

@macro
def sum(*arguments: AnyDensity) -> Density[types.add]:
    "Returns the sum of any number of arguments."
    if len(arguments) == 0:
        return Density.constant(0)
    if len(arguments) == 1:
        return arguments[0]
    
    it = iter(arguments)
    result = next(it) + next(it)

    for x in it:
        result = result + x

    return result

@macro
def prod(*arguments: AnyDensity) -> Density[types.mul]:
    "Returns the product of any number of arguments."
    if len(arguments) == 0:
        return Density.constant(0)
    if len(arguments) == 1:
        return arguments[0]
    
    it = iter(arguments)
    result = next(it) * next(it)

    for x in it:
        result = result * x

    return result

@macro
def floordiv(dividend: AnyDensity, divisor: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.range_choice]:
    """Returns the floor division of two inputs (`argument1 // argument2`) within the specified range.
    Values where the quotient falls outside this range's rounding intervals will be left unrounded."""
    return floor(dividend / divisor, range=range)

@macro
def mod(dividend: AnyDensity, divisor: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.add]:
    """Returns the modulo of two inputs (`argument1 % argument2`) within the specified range.
    Values where the quotient falls outside this range's rounding intervals will not be calculated as true modulo."""
    return perf.autocache(dividend - divisor * floor(dividend / divisor, range=range))

#======// Step Functions //======================================================================//

@macro
def sgn(argument: AnyDensity) -> Density[types.range_choice]:
    """Returns `1.0` when the input is positive, `-1.0` when it's negative and itself when it's `0.0`."""
    return cond.when(argument).equals(0.0).then(0.0).elsewhen(cond.it).less(0.0).then(-1.0).otherwise(1.0)

@macro
def heaviside(argument: AnyDensity, *, at_zero: AnyDensity = 0.5) -> Density[types.range_choice]:
    "Returns the Heaviside function value of the input which is `0.0` when the input is negative and `1.0` when it is positive."
    return cond.when(argument).equals(0.0).then(at_zero).elsewhen(cond.it).less(0.0).then(0.0).otherwise(1.0)

@macro
def monus(argument1: AnyDensity, argument2: AnyDensity):
    """Returns `argument1 - argument2`, but when that's negative, returns `0.0` instead."""
    return f.max(argument1 - argument2, 0.0)

@macro
def ramp(argument: AnyDensity) -> Density[types.max]:
    """Returns the ramp function value of the input, meaning `argument1` itself, when it's positive, otherwise returns `0.0`."""
    return f.max(argument, 0)

@macro
def round(argument: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.range_choice]:
    """Rounds the input to the nearest integer within the specified range.
    Values outside this range's rounding intervals will be left unrounded."""
    start_int = py_math.ceil(range[0])
    end_int = py_math.floor(range[1])
    
    if start_int > end_int:
        raise ValueError("'range' requires a lower and upper bound")
        
    expr = cond.when(argument).between(start_int - 0.5, start_int + 0.5).then(float(start_int))
    
    i = start_int + 1
    while i <= end_int:
        expr = expr.elsewhen(cond.it).between(i - 0.5, i + 0.5).then(float(i))
        i += 1
        
    return expr.otherwise(cond.it)

@macro
def floor(argument: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.range_choice]:
    """Rounds the input down to the nearest integer within the specified range.
    Values outside this range's rounding intervals will be left unrounded."""
    from rhombus import config
    EPS = config.infinitesimal
    
    start_int = py_math.floor(range[0])
    end_int = py_math.floor(range[1])
    
    if start_int > end_int:
        raise ValueError("'range' requires a lower and upper bound")
        
    expr = cond.when(argument).between(start_int, start_int + 1.0 - EPS).then(float(start_int))
    
    i = start_int + 1
    while i <= end_int:
        expr = expr.elsewhen(cond.it).between(i, i + 1.0 - EPS).then(float(i))
        i += 1
        
    return expr.otherwise(cond.it)

@macro
def ceil(argument: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.range_choice]:
    """Rounds the input up to the nearest integer within the specified range.
    Values outside this range's rounding intervals will be left unrounded."""
    from rhombus import config
    EPS = config.infinitesimal
    
    start_int = py_math.ceil(range[0])
    end_int = py_math.ceil(range[1])
    
    if start_int > end_int:
        raise ValueError("'range' requires a lower and upper bound")
        
    expr = cond.when(argument).between(start_int - 1.0 + EPS, start_int).then(float(start_int))
    
    i = start_int + 1
    while i <= end_int:
        expr = expr.elsewhen(cond.it).between(i - 1.0 + EPS, i).then(float(i))
        i += 1
        
    return expr.otherwise(cond.it)


#======// Approximations //======================================================================//

@macro
def sqrt_linear_01(argument: AnyDensity) -> Density[types.add]:
    return 0.41731 + 0.59016*argument

@macro
def sqrt_rational_01(argument: AnyDensity) -> Density[types.mul]:
    return argument / (0.41731+0.59016*argument)