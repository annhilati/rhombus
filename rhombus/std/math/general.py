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
    "sqrt",
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
    "sign",
    "monus",
    "spline",
    "sample_spline_points",
    "poly_spline_points",
    "spline_points_to_cubics",
]

import builtins as py_builtins

from rhombus.std.builtin.density import Density, AnyDensity
from rhombus.std.builtin.macros import macro, implementation
from rhombus.std import caching
import rhombus.support.vanilla.types as vt


# ======// Constants //==========================================================================//

Infinity = macro(lambda: Density(1) / 0, repr=lambda n: "Infinity")()
"Density equivalent to Java's `Float.POSITIVE_INFINITY`."

@macro(repr=lambda n: "NaN")
def _nan() -> Density:
    @implementation(until=111)
    def legacy():
        return Density(vt.mul(vt.constant(0.0), vt.reciprocal(vt.constant(0.0))))
    @implementation
    def modern():
        return Density(vt.sqrt(vt.constant(-1)))

NaN = _nan()
"""Density equivalent to Java's `Float.NaN`.

**NOTE:** All arithmetic operations with `NaN` will result in `NaN`. Before
chunk generation, `NaN` will be casted to `0.0` thus it will be interpreted 
as air.
"""

e = 2.7182818284590452 # 35360287471352662497757247093699959574966
"Euler's number `e` to 16 decimals."
sqrt2 = 1.4142135623730950 # 48801688724209
"The square root of 2 to 16 decimals."
phi = 1.6180339887498948 # 4820458683436563811772030917980576
"The golden ratio to 16 decimals."

def constant(value: float) -> Density:
    """Declares a constant float value."""
    return Density(value)


# ======// Arithmetic //==========================================================================//
# NOTE: The selection of functions here may not seem optimal, but some functions yield the
#       implementations for the operators of the Density class, which I figured are in good hands here.


@macro
def sum(*dfs: AnyDensity) -> Density:
    "Calculates the sum of any number of arguments."
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return dfs[0]

    it = iter(dfs)
    result = vt.add(next(it).build(), next(it).build())

    for x in it:
        result = vt.add(result, x.build())

    return Density(result)


@macro
def prod(*dfs: AnyDensity) -> Density:
    "Calculates the product of any number of arguments."
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return dfs[0]

    it = iter(dfs)
    result = vt.mul(next(it).build(), next(it).build())

    for x in it:
        result = vt.mul(result, x.build())

    return Density(result)


@macro(repr=lambda n: f"({' + '.join(repr(a) for a in n.args)})" if n.args else "0")
def add(*dfs: AnyDensity) -> Density:
    """Calculates the sum of any number of arguments."""
    return sum(*dfs)


@macro(repr=lambda n: f"({n.args[0] if len(n.args) > 0 else n.kwargs["minuend"]!r} - {n.args[1] if len(n.args) > 1 else n.kwargs["subtrahend"]!r})")
def sub(minuend: AnyDensity, subtrahend: AnyDensity) -> Density:
    """Caluclates the difference of two arguments."""
    @implementation(until=111)
    def sub():
        return Density(vt.add(minuend.build(), vt.mul(-1, subtrahend.build())))
    @implementation
    def sub():
        return Density(vt.sub(minuend.build(), subtrahend.build()))


@macro(repr=lambda n: f"({' * '.join(repr(a) for a in n.args)})" if n.args else "0")
def mul(*dfs: AnyDensity) -> Density:
    """Calculates the product of any number of arguments."""
    return prod(*dfs)


@macro(repr=lambda n: f"({n.args[0] if len(n.args) > 0 else n.kwargs["dividend"]!r} / {n.args[1] if len(n.args) > 1 else n.kwargs["divisor"]!r})")
def div(dividend: AnyDensity, divisor: AnyDensity) -> Density:
    """Calculates the quotient of two arguments."""
    @implementation(until=111)
    def div():
        if isinstance(divisor_build := divisor.build(), vt.constant):
            return dividend * Density(1 / divisor_build.value)
        if isinstance(dividend_build := dividend.build(), vt.constant) and dividend_build.value == 1:
            return Density(vt.reciprocal(divisor_build))
        return Density(vt.mul(dividend.build(), vt.reciprocal(divisor.build())))
    @implementation
    def div():
        if isinstance(dividend_build := dividend.build(), vt.constant) and dividend_build.value == 1:
            return Density(vt.reciprocal(divisor.build()))
        return Density(vt.div(dividend.build(), divisor.build()))


@macro
def abs(df: AnyDensity) -> Density:
    """Returns the absolute value of the input."""
    return Density(vt.abs(df.build()))


@macro(repr=lambda n: f"- {n.args[0] if len(n.args) > 0 else n.kwargs["df"]!r}")
def neg(df: AnyDensity) -> Density:
    """Negates the values of the input."""
    @implementation(until=111)
    def neg():
        return df * -1
    
    @implementation
    def neg():
        return Density(vt.negate(df.build()))


@macro(repr=lambda n: f"({n.args[0] if len(n.args) > 0 else n.kwargs["base"]!r} ** {n.args[1] if len(n.args) > 1 else n.kwargs["exponent"]!r})")
def pow(base: AnyDensity, exponent: AnyDensity) -> Density:
    """Raises the input to an arbitrary power. Since `exponent` can be a fraction, roots can also be calculated.
    
    **NOTE:** In datapack versions below 113, only integer exponents are supported.
    """
    @implementation(until=113)
    def pow():
        built_exponent = exponent.build()
        if not isinstance(built_exponent, vt.constant):
            raise ValueError("Can only raise to integer powers in datapack versions below 113")
        if 0 <= py_builtins.abs(built_exponent.value) <= 3:
            result = {
                0: Density(vt.constant(1)),
                1: base,
                2: Density(vt.square(base.build())),
                3: Density(vt.cube(base.build()))
            }[py_builtins.int(built_exponent.value)]
        else:
            result = base
            for _ in range(py_builtins.abs(built_exponent.value) - 1):
                result = Density(vt.mul(result.build(), base.build()))
        if built_exponent.value < 0:
            result = Density(vt.reciprocal(result.build()))
        return result
    
    @implementation
    def pow():
        if exponent.AST == Density(0.5).AST:
            return Density(vt.sqrt(base.build()))
        return Density(vt.pow(base.build(), exponent.build()))


@macro
def sqrt(df: AnyDensity) -> Density:
    "Calculates the square root of the input."
    @implementation(since=111)
    def sqrt():
        return Density(vt.sqrt(df.build()))


@macro
def log(df: AnyDensity, *, base: AnyDensity = e) -> Density:
    "Calculates the logarithm of the input to an arbitrary base."
    @implementation(since=111)
    def log():
        if base.AST == Density(e).AST:
            return Density(vt.log(df.build()))
        return Density(vt.log(df.build())) / Density(vt.log(base.build()))


# ======// Ordering //===========================================================================//


@macro
def clamp(df: AnyDensity, min: AnyDensity, max: AnyDensity) -> Density:
    """Limits the values of the input to the range `[min, max]`."""
    built_min = min.build()
    built_max = max.build()
    if isinstance(built_min, vt.constant) and isinstance(built_max, vt.constant):
        return Density(vt.clamp(df.build(), built_min.value, built_max.value))
    return Density(vt.max(max.build(), vt.min(min.build(), df.build())))


@macro
def min(*dfs: AnyDensity) -> Density:
    "Returns the minimum of any number of arguments."
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return dfs[0]

    it = iter(dfs)
    result = vt.min(next(it).build(), next(it).build())

    for x in it:
        result = vt.min(result, x.build())

    return Density(result)


@macro
def max(*dfs: AnyDensity) -> Density:
    "Returns the maximum of any number of arguments."
    if len(dfs) == 0:
        return Density(0)
    if len(dfs) == 1:
        return dfs[0]

    it = iter(dfs)
    result = vt.max(next(it).build(), next(it).build())

    for x in it:
        result = vt.max(result, x.build())

    return Density(result)


# Reference: https://www.youtube.com/watch?v=6Qb6QtC6QMs
@macro
def smax(
    *dfs: AnyDensity, smoothing_factor: AnyDensity = 0.1, degree: int = 3
) -> Density:
    """Calculates a smooth maximum of any number of arguments.

    This function uses a piecewise polynomial approximation to smooth out the hard
    edges of the regular `max()` function.

    Parameters:
        smoothing_factor (AnyDensity): Defines the interval `[-smoothing_factor, smoothing_factor]`
            around intersections where the blending occurs.
            Outside this distance, the function behaves exactly like the regular `max()`.
        degree (int): Polynomial degree used for the interpolation.
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


# Reference: https://www.youtube.com/watch?v=6Qb6QtC6QMs
@macro
def smin(
    *dfs: AnyDensity, smoothing_factor: AnyDensity = 0.1, degree: int = 3
) -> Density:
    """Calculates a smooth minimum of any number of arguments.

    This function uses a piecewise polynomial approximation to smooth out the hard
    edges of the regular `min()` function.

    Parameters:
        smoothing_factor (AnyDensity): Defines the interval `[-smoothing_factor, smoothing_factor]`
            around intersections where the blending occurs.
            Outside this distance, the function behaves exactly like the regular `max()`.
        degree (int): Polynomial degree used for the interpolation.
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
    """Rounds the input to the nearest integer or a given decimal place."""
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
        return Density(vt.round(df.build(), 10**-decimals))


@macro
def floor(df: AnyDensity, decimals: int = 0) -> Density:
    """Rounds the input down to the nearest integer or a given decimal place."""
    @implementation(until=111)
    def floor():
        if decimals:
            return round((df - 0.5) * 10**decimals) / 10**decimals
        return round(df - 0.5)
    
    @implementation
    def floor():
        return Density(vt.floor(df.build(), 10**-decimals))


@macro
def ceil(df: AnyDensity, decimals: int = 0) -> Density:
    """Rounds the input up to the nearest integer or a given decimal place."""
    @implementation(until=111)
    def floor():
        if decimals:
            return round((df + 0.5) * 10**decimals) / 10**decimals
        return round(df + 0.5)
    
    @implementation
    def floor():
        return Density(vt.ceil(df.build(), 10**-decimals))


@macro
def truncate(df: AnyDensity, decimals: int = 0) -> Density:
    """Truncates (rounding towards zero) the input to the nearest integer or a given decimal place."""
    @implementation(since=111)
    def truncate():
        return Density(vt.truncate(df.build(), 10**-decimals))


@macro(repr=lambda n: f"({n.args[0] if len(n.args) > 0 else n.kwargs["dividend"]!r} // {n.args[1] if len(n.args) > 1 else n.kwargs["divisor"]!r})")
def floordiv(dividend: AnyDensity, divisor: AnyDensity) -> Density:
    """Calculates the quotient of two arguments and discards the remainder."""
    return floor(dividend / divisor)


@macro(repr=lambda n: f"({n.args[0] if len(n.args) > 0 else n.kwargs["dividend"]!r} % {n.args[1] if len(n.args) > 1 else n.kwargs["modulus"]!r})")
def mod(dividend: AnyDensity, modulus: AnyDensity) -> Density:
    """Calculates the remainder of the division of two arguments."""
    return caching.optimize(
        dividend - modulus * floor(dividend / modulus),
        targets=(dividend, modulus),
        min_size=5
    )


# ======// Step Functions //======================================================================//


@macro
def sign(df: AnyDensity) -> Density:
    """Returns `1.0` when the input is positive, `-1.0` when it's negative and itself when it's `0.0`."""
    @implementation(until=113)
    def sign():
        if df == 0:
            return Density(0)
        elif df < 0:
            return Density(-1)
        else:
            return Density(1)
        
    @implementation
    def sign():
        return Density(vt.sign(df.build()))


@macro
def heaviside(df: AnyDensity, *, at_zero: AnyDensity = 0.5) -> Density:
    "Returns `0.0` when the input is negative and `1.0` when it is positive."
    if df == 0:
        return at_zero
    elif df < 0:
        return 0
    else:
        return 1


@macro
def monus(minuend: AnyDensity, subtrahend: AnyDensity):
    """Returns `argument1 - argument2`, but when that's negative, returns `0.0` instead."""
    return max(minuend - subtrahend, 0.0)


# ======// Splines //============================================================================//


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
    defined values will be returned. ("first" and "second" refer to the order of their
    **definition** in `points`).
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#spline) • [Wikipedia](https://en.wikipedia.org/wiki/Cubic_Hermite_spline)
    """
    def convert_point(p: tuple[float, AnyDensity, float]):
        location, value, derivative = p
        value_build = value.build()
        
        if isinstance(value_build, vt.spline):
            value_build = value_build.spline
            
        return vt.SplinePoint(location, value_build, derivative)

    ast_points = [convert_point(p) for p in points]
    return Density(vt.spline(vt.SplineConfig(input.build(), ast_points)))


# Redirect imports
from rhombus.std.math._splinelib import sample_spline_points, poly_spline_points, spline_points_to_cubics