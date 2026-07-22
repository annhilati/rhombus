"""Macro module for general mathematical functions and constants."""

from rhombus.std import Density, AnyDensity, f, types, macro
from rhombus.macros import conditional as cond, performance as perf

__all__ = [
    "Infinity",
    "NaN",
    "pi",
    "e",
    "sum",
    "prod",
    "min",
    "max",
    "smin",
    "smax",
    "round",
    "floor",
    "ceil",
    "round",
    "floor",
    "ceil",
    "mod",
    "floordiv",
    "heaviside",
    "ramp",
    "sgn",
    "monus",
    "sqrt_linear_01",
    "sqrt_rational_01",
]

# ======// Numeric Constants //===================================================================//

Infinity = Density(1) / 0
"Density equivalent to Java's `Double.POSITIVE_INFINITY`"
NaN = Density(0) / 0
"""Density equivalent to Java's `Double.NaN`

**NOTE:** All arithmetic operations with `NaN` will result in `NaN`. Before
chunk generation, `NaN` will be casted to `0.0` thus it will be interpreted 
as air.
"""

pi = 3.1415926535897932  # 38462643383279502884197169399375105820974944592307816406
"The constant `π` to 16 decimals."
e  = 2.7182818284590452  # 35360287471352662497757247093699959574966
"Euler's number `e` to 16 decimals."


# ======// Arithmetic //==========================================================================//


@macro
def sum(*arguments: AnyDensity) -> Density[types.add]:
    "Returns the sum of any number of arguments."
    if len(arguments) == 0:
        return Density(0)
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
        return Density(0)
    if len(arguments) == 1:
        return arguments[0]

    it = iter(arguments)
    result = next(it) * next(it)

    for x in it:
        result = result * x

    return result


@macro
def min(*arguments: AnyDensity) -> Density[types.min]:
    "Returns the minimum of any number of arguments."
    if len(arguments) == 0:
        return Density(0)
    if len(arguments) == 1:
        return arguments[0]

    it = iter(arguments)
    result = next(it) | next(it)

    for x in it:
        result = result | x

    return result


@macro
def max(*arguments: AnyDensity) -> Density[types.max]:
    "Returns the maximum of any number of arguments."
    if len(arguments) == 0:
        return Density(0)
    if len(arguments) == 1:
        return arguments[0]

    it = iter(arguments)
    result = next(it) & next(it)

    for x in it:
        result = result & x

    return result


@macro
def smax(*arguments: AnyDensity, smoothing_factor: AnyDensity = 0.1, degree: int = 3) -> Density:
    """Returns the smooth maximum of any number of arguments.
    
    This function uses a piecewise polynomial approximation to smooth out the hard 
    edges of the regular `max()` function.
    
    Parameters:
        smoothing_factor (AnyDensity): The smoothing radius (lambda). It defines the interval
            `[-smoothing_factor, smoothing_factor]` around the intersection where the blending occurs. 
            Outside this distance, the function behaves exactly like the regular `max()`.
        degree (int): The polynomial degree used for the interpolation. 
            `2` = quadratic, `3` = cubic (default), `4` = quartic, etc.
            Higher degrees yield smoother derivatives at the boundary.
    """
    if len(arguments) == 0:
        return Density(0)
    if len(arguments) == 1:
        return Density(arguments[0])

    it = iter(arguments)
    result = next(it)

    for x in it:
        diff_clamped = max(smoothing_factor - f.abs(result - x), 0.0)
        power = diff_clamped ** degree
        denominator = (2 * degree) * (smoothing_factor ** (degree - 1))
        
        result = max(result, x) + (power / denominator)

    return result


@macro
def smin(*arguments: AnyDensity, smoothing_factor: AnyDensity = 0.1, degree: int = 3) -> Density:
    """Returns the smooth minimum of any number of arguments.
    
    This function uses a piecewise polynomial approximation to smooth out the hard 
    edges of the regular `min()` function.
    
    Parameters:
        smoothing_factor (AnyDensity): The smoothing radius (lambda). It defines the interval
            `[-smoothing_factor, smoothing_factor]` around the intersection where the blending occurs. 
            Outside this distance, the function behaves exactly like the regular `min()`.
        degree (int): The polynomial degree used for the interpolation. 
            `2` = quadratic, `3` = cubic (default), `4` = quartic, etc.
            Higher degrees yield smoother derivatives at the boundary.
    """
    if len(arguments) == 0:
        return Density(0)
    if len(arguments) == 1:
        return Density(arguments[0])

    it = iter(arguments)
    result = next(it)

    for x in it:
        diff_clamped = max(smoothing_factor - f.abs(result - x), 0.0)
        power = diff_clamped ** degree
        denominator = (2 * degree) * (smoothing_factor ** (degree - 1))
        
        result = min(result, x) - (power / denominator)

    return result


# ======// Rounding //============================================================================//


@macro
def round(argument: AnyDensity, decimals: int = 0) -> Density[types.add]:
    """Rounds the input to the nearest integer or given decimal.

    **NOTE:** This implementation exploits the IEEE 754 Java Double implementation, which means
    that it will not work, when other number types are in use.
    """
    if decimals:
        return (
            (argument * 10**decimals)
            + f.constant(1.5) * f.constant(2**52)
            - f.constant(1.5) * f.constant(2**52)
        ) / 10**decimals
    return (
        argument
        + f.constant(1.5) * f.constant(2**52)
        - f.constant(1.5) * f.constant(2**52)
    )


@macro
def floor(argument: AnyDensity, decimals: int = 0) -> Density[types.add]:
    """Rounds the input down to the nearest integer or given decimal.

    **NOTE:** This implementation exploits the IEEE 754 Java Double implementation, which means
    that it will not work, when other number types are in use.
    """
    if decimals:
        return round((argument - 0.5) * 10**decimals) / 10**decimals
    return round(argument - 0.5)


@macro
def ceil(argument: AnyDensity, decimals: int = 0) -> Density[types.add]:
    """Rounds the input up to the nearest integer or given decimal.

    **NOTE:** This implementation exploits the IEEE 754 Java Double implementation, which means
    that it will not work, when other number types are in use.
    """
    if decimals:
        return round((argument + 0.5) * 10**decimals) / 10**decimals
    return round(argument + 0.5)


@macro
def floordiv(dividend: AnyDensity, divisor: AnyDensity) -> Density[types.range_choice]:
    """Returns the floor division of two inputs (`argument1 // argument2`).

    **NOTE:** This implementation exploits the IEEE 754 Java Double implementation, which means
    that it will not work, when other number types are in use.
    """
    return floor(dividend / divisor)


@macro
def mod(dividend: AnyDensity, divisor: AnyDensity) -> Density[types.add]:
    """Returns the modulo of two inputs (`argument1 % argument2`).

    **NOTE:** This implementation exploits the IEEE 754 Java Double implementation, which means
    that it will not work, when other number types are in use.
    """
    return perf.specified_cache(
        dividend - divisor * floor(dividend / divisor), dividend, divisor
    )


# ======// Step Functions //======================================================================//


@macro
def sgn(argument: AnyDensity) -> Density[types.range_choice]:
    """Returns `1.0` when the input is positive, `-1.0` when it's negative and itself when it's `0.0`."""
    return (
        cond.when(argument)
        .equals(0.0)
        .then(0.0)
        .elsewhen(cond.it)
        .less(0.0)
        .then(-1.0)
        .otherwise(1.0)
    )


@macro
def heaviside(
    argument: AnyDensity, *, at_zero: AnyDensity = 0.5
) -> Density[types.range_choice]:
    "Returns the Heaviside function value of the input which is `0.0` when the input is negative and `1.0` when it is positive."
    return (
        cond.when(argument)
        .equals(0.0)
        .then(at_zero)
        .elsewhen(cond.it)
        .less(0.0)
        .then(0.0)
        .otherwise(1.0)
    )


@macro
def monus(argument1: AnyDensity, argument2: AnyDensity):
    """Returns `argument1 - argument2`, but when that's negative, returns `0.0` instead."""
    return f.max(argument1 - argument2, 0.0)


@macro
def ramp(argument: AnyDensity) -> Density[types.max]:
    """Returns the ramp function value of the input, meaning `argument1` itself, when it's positive, otherwise returns `0.0`."""
    return f.max(argument, 0)


# ======// Approximations //======================================================================//


@macro
def sqrt_linear_01(argument: AnyDensity) -> Density[types.add]:
    return 0.41731 + 0.59016 * argument


@macro
def sqrt_rational_01(argument: AnyDensity) -> Density[types.mul]:
    return argument / (0.41731 + 0.59016 * argument)
