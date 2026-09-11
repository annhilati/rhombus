"""Macro module for general mathematical functions and constants."""

__all__ = [
    "Infinity",
    "NaN",
    "e",
    "constant",
    "add",
    "sub",
    "mul",
    "div",
    "neg",
    "abs",
    # "square",
    # "cube",
    "pow",
    "log",
    "sum",
    "prod",
    "clamp",
    "min",
    "max",
    "smin",
    "smax",
    "round",
    "floor",
    "ceil",
    "truncate",
    "mod",
    "floordiv",
    "heaviside",
    "ramp",
    "sign",
    "monus",
    "spline"
]

import builtins as py_builtins

from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro, implementation
from rhombus.std import conditional as cond, caching
from rhombus.support import vanilla as vt, vanilla_legacy as lt


# ======// Constants //==========================================================================//

# TODO: Check whether we can make the UnresolvedMacroNode API more open and define one here instead of using a complete macro definition
@macro
def _infinity() -> Density:
    @implementation(until=111)
    def _legacy():
        return Density(vt.mul(1, vt.reciprocal(0)))
    @implementation
    def _modern():
        return Density(vt.div(1, 0))

Infinity = _infinity()
"Density equivalent to Java's `Float.POSITIVE_INFINITY`."

@macro
def _nan() -> Density:
    @implementation(until=111)
    def _legacy():
        return Density(vt.mul(0, vt.reciprocal(0)))
    @implementation
    def _modern():
        return Density(vt.div(0, 0))

NaN = _nan()
"""Density equivalent to Java's `Float.NaN`.

**NOTE:** All arithmetic operations with `NaN` will result in `NaN`. Before
chunk generation, `NaN` will be casted to `0.0` thus it will be interpreted 
as air.
"""

e = 2.7182818284590452 # 35360287471352662497757247093699959574966
"Euler's number `e` to 16 decimals."


def constant(value: float) -> Density:
    """Declares a constant float value."""
    return Density(value)


# ======// Arithmetic //==========================================================================//
# NOTE: The selection of functions here may not seem optimal, but some functions yield the
#       implementations for the operators of the Density class, which I figured are in good hands here.


@macro
def add(df1: AnyDensity, df2: AnyDensity) -> Density:
    """Returns the sum of two inputs."""
    return Density(vt.add(df1.AST, df2.AST))


@macro
def sub(minuend: AnyDensity, subtrahend: AnyDensity) -> Density:
    """Returns the difference of two inputs."""
    @implementation(until=111)
    def sub():
        return Density(vt.add(minuend.AST, vt.mul(-1, subtrahend.AST)))
    @implementation
    def sub():
        return Density(vt.sub(minuend.AST, subtrahend.AST))


@macro
def mul(df1: AnyDensity, df2: AnyDensity) -> Density:
    """Returns the product of two inputs."""
    return Density(vt.mul(df1.AST, df2.AST))


@macro
def div(dividend: AnyDensity, divisor: AnyDensity) -> Density:
    """Returns the quotient of two inputs."""
    @implementation(until=111)
    def div():
        return Density(vt.mul(dividend.AST, vt.reciprocal(divisor.AST)))
    @implementation
    def div():
        return Density(vt.div(dividend.AST, divisor.AST))


@macro
def abs(df: AnyDensity) -> Density:
    """Returns the absolute value of the input."""
    return Density(vt.abs(df.AST))


@macro
def neg(df: AnyDensity) -> Density:
    """Negates the values of the input."""
    @implementation(until=111)
    def neg():
        return df * -1
    
    @implementation
    def neg():
        return Density(vt.negate(df.AST))


# @macro
# def square(df: AnyDensity) -> Density:
#     """Raises the input to the power of 2."""
#     return Density(vt.square(df.AST))


# @macro
# def cube(df: AnyDensity) -> Density:
#     """Raises the input to the power of 3."""
#     return Density(vt.cube(df.AST))


@macro
def pow(base: AnyDensity, exponent: AnyDensity) -> Density:
    """Raises the input to an arbitrary power. Since the `exponent` can be a fraction, square roots are also possible.
    
    **NOTE:** In datapack versions below 113, only integer exponents are supported.
    """
    @implementation(until=113)
    def pow():
        if not isinstance(exponent, int):
            raise ValueError("Can only raise to integer powers in datapack versions below 113")
        if 0 <= py_builtins.abs(exponent) <= 3:
            result = {
                0: Density(vt.constant(1)),
                1: base,
                2: Density(vt.square(base.AST)),
                3: Density(vt.cube(base.AST))
            }[exponent]
        else:
            result = base
            for _ in range(py_builtins.abs(exponent) - 1):
                result = Density(vt.mul(result.AST, base.AST))
        if exponent < 0:
            result = Density(vt.reciprocal(result.AST))
        return result
    
    @implementation
    def pow():
        if exponent == Density(0.5):
            return Density(vt.sqrt(base.AST))
        return Density(vt.pow(base.AST, exponent.AST))


@macro
def log(df: AnyDensity, *, base: AnyDensity = e):
    if base == Density(e):
        return vt.log(df.AST)
    return vt.log(df.AST) / vt.log(base.AST)


@macro
def sum(*dfs: AnyDensity) -> Density:
    "Returns the sum of any number of arguments."
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return dfs[0]

    it = iter(dfs)
    result = next(it) + next(it)

    for x in it:
        result = result + x

    return result


@macro
def prod(*dfs: AnyDensity) -> Density:
    "Returns the product of any number of arguments."
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return dfs[0]

    it = iter(dfs)
    result = next(it) * next(it)

    for x in it:
        result = result * x

    return result


# ======// Ordering //===========================================================================//


@macro
def clamp(df: AnyDensity, min: float, max: float) -> Density:
    """Returns the larger value from the input and min, and the smaller value from that and max."""
    return Density(vt.clamp(df.AST, min, max))


@macro
def min(*dfs: AnyDensity) -> Density:
    "Returns the minimum of any number of arguments."
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return dfs[0]

    it = iter(dfs)
    result = vt.min(next(it.AST), next(it.AST))

    for x in it:
        result = vt.min(result, x.AST)

    return Density(result)


@macro
def max(*dfs: AnyDensity) -> Density:
    "Returns the maximum of any number of arguments."
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return dfs[0]

    it = iter(dfs)
    result = vt.max(next(it.AST), next(it.AST))

    for x in it:
        result = vt.max(result, x.AST)

    return Density(result)


@macro
def smax(
    *dfs: AnyDensity, smoothing_factor: AnyDensity = 0.1, degree: int = 3
) -> Density:
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
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return Density(dfs[0])

    it = iter(dfs)
    result = next(it)

    for x in it:
        diff_clamped = max(smoothing_factor - py_builtins.abs(result - x), 0.0)
        power = diff_clamped**degree
        denominator = (2 * degree) * (smoothing_factor ** (degree - 1))

        result = max(result, x) + (power / denominator)

    return result


@macro
def smin(
    *dfs: AnyDensity, smoothing_factor: AnyDensity = 0.1, degree: int = 3
) -> Density:
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
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return Density(dfs[0])

    it = iter(dfs)
    result = next(it)

    for x in it:
        diff_clamped = max(smoothing_factor - py_builtins.abs(result - x), 0.0)
        power = diff_clamped**degree
        denominator = (2 * degree) * (smoothing_factor ** (degree - 1))

        result = min(result, x) - (power / denominator)

    return result


# ======// Rounding //============================================================================//


@macro
def round(df: AnyDensity, decimals: int = 0) -> Density:
    """Rounds the input to the nearest integer or given decimal."""
    @implementation(until=111)
    def round():
        if decimals:
            return (
                df * 10**decimals
                + constant(1.5) * constant(2**52)
                - constant(1.5) * constant(2**52)
            ) / 10**decimals
        return (
            df + constant(1.5) * constant(2**52) - constant(1.5) * constant(2**52)
        )
    
    @implementation
    def round():
        return Density(vt.round(df.AST, 10**-decimals))


@macro
def floor(df: AnyDensity, decimals: int = 0) -> Density:
    """Rounds the input down to the nearest integer or given decimal."""
    @implementation(until=111)
    def floor():
        if decimals:
            return round((df - 0.5) * 10**decimals) / 10**decimals
        return round(df - 0.5)
    
    @implementation
    def floor():
        return Density(vt.floor(df.AST, 10**-decimals))


@macro
def ceil(df: AnyDensity, decimals: int = 0) -> Density:
    """Rounds the input up to the nearest integer or given decimal."""
    @implementation(until=111)
    def floor():
        if decimals:
            return round((df + 0.5) * 10**decimals) / 10**decimals
        return round(df + 0.5)
    
    @implementation
    def floor():
        return Density(vt.ceil(df.AST, 10**-decimals))


@macro
def truncate(df: AnyDensity, decimals: int = 0) -> Density:
    """Truncates the input to the nearest integer or given decimal. This is equivalent to rounding towards to zero."""
    return Density(vt.truncate(df.AST, 10**-decimals))


@macro
def floordiv(dividend: AnyDensity, divisor: AnyDensity) -> Density:
    """Returns the floor division of two inputs (`argument1 // argument2`)."""
    return floor(dividend / divisor)


@macro
def mod(dividend: AnyDensity, divisor: AnyDensity) -> Density:
    """Returns the modulo of two inputs (`argument1 % argument2`)."""
    return caching.specified_cache(
        dividend - divisor * floor(dividend / divisor), dividend, divisor
    )
    # TODO: do not cache small functions


# ======// Step Functions //======================================================================//


@macro
def sign(df: AnyDensity) -> Density:
    """Returns `1.0` when the input is positive, `-1.0` when it's negative and itself when it's `0.0`."""
    @implementation(until=113)
    def sign():
        return (
            cond.when(df)
            .equals(0.0)
            .then(0.0)
            .elsewhen(cond.it)
            .less(0.0)
            .then(-1.0)
            .otherwise(1.0)
        )
        
    @implementation
    def sign():
        return Density(vt.sign(df.AST))


@macro
def heaviside(df: AnyDensity, *, at_zero: AnyDensity = 0.5) -> Density:
    "Returns the Heaviside function value of the input which is `0.0` when the input is negative and `1.0` when it is positive."
    return (
        cond.when(df)
        .equals(0.0)
        .then(at_zero)
        .elsewhen(cond.it)
        .less(0.0)
        .then(0.0)
        .otherwise(1.0)
    )


@macro
def monus(minuend: AnyDensity, subtrahend: AnyDensity):
    """Returns `argument1 - argument2`, but when that's negative, returns `0.0` instead."""
    return max(minuend - subtrahend, 0.0)


@macro
def ramp(df: AnyDensity) -> Density:
    """Returns the ramp function value of the input, meaning `argument1` itself, when it's positive, otherwise returns `0.0`."""
    return max(df, 0)


# ======// Spline //=============================================================================//


@macro
def spline(
    input: AnyDensity, points: list[tuple[float, AnyDensity, float]]
) -> Density:
    """Computes the value of a cubic spline for the input.

    The values for the points represent in order: `location`, `value` and `derivative`.

    For values beyond the outermost spline points, the value of the nearest spline point is returned.

    **NOTE:** If multiple spline points have the same location, for inputs less than the
    location, values aproaching the first defined value will be returned. For
    inputs equal to or greather than the location, values leaving the second
    defined values will be returned. ("first" and "second" refer to the order
    of **definition** in `points`).
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#spline) • [Wikipedia](https://en.wikipedia.org/wiki/Cubic_Hermite_spline)
    """
    points = [(p[0], p[1].AST, p[2]) for p in points]
    return Density(vt.spline(input.AST, points))