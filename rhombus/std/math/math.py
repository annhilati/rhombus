"""Macro module for general mathematical functions and constants."""

__all__ = [
    "Infinity",
    "NaN",
    "pi",
    "e",
    "constant",
    "add",
    "sub",
    "mul",
    "div",
    "square",
    "cube",
    "pow",
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
    "sgn",
    "monus",
    "spline"
]

from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro
from rhombus.std import conditional as cond, caching
from rhombus.support import vanilla as vt, vanilla_legacy as lt

from rhombus.core.environment import env


# ======// Constants //==========================================================================//

Infinity = Density(1) / 0
"Density equivalent to Java's `Double.POSITIVE_INFINITY`"
NaN = Density(0) / 0
"""Density equivalent to Java's `Double.NaN`

**NOTE:** All arithmetic operations with `NaN` will result in `NaN`. Before
chunk generation, `NaN` will be casted to `0.0` thus it will be interpreted 
as air.
"""

e = Density(2.7182818284590452)  # 35360287471352662497757247093699959574966
"Euler's number `e` to 16 decimals."


def constant(value: float) -> Density[vt.constant]:
    """Declares a constant float value."""
    return Density(value)


# ======// Arithmetic //==========================================================================//


@macro
def add(df1: AnyDensity, df2: AnyDensity) -> Density[vt.add]:
    """Returns the sum of two inputs."""
    return Density(vt.add(df1.AST, df2.AST))


@macro
def sub(minuend: AnyDensity, subtrahend: AnyDensity) -> Density[vt.add]:
    """Returns the difference of two inputs."""
    if env.datapack_version is not None and env.datapack_version < 111:
        return Density(vt.add(minuend.AST, vt.mul(-1, subtrahend.AST)))
    else:
        return Density(vt.sub(minuend.AST, subtrahend.AST))


@macro
def mul(df1: AnyDensity, df2: AnyDensity) -> Density[vt.mul]:
    """Returns the product of two inputs."""
    return Density(vt.mul(df1.AST, df2.AST))


@macro
def div(dividend: AnyDensity, divisor: AnyDensity) -> Density[vt.mul]:
    """Returns the quotient of two inputs."""
    if env.datapack_version is not None and env.datapack_version < 111:
        return Density(vt.mul(dividend.AST, vt.reciprocal(divisor.AST)))
    else:
        return Density(vt.div(dividend.AST, divisor.AST))


@macro
def square(df: AnyDensity) -> Density[vt.square]:
    """Raises the input to the power of 2."""
    return Density(vt.square(df.AST))


@macro
def cube(df: AnyDensity) -> Density[vt.cube]:
    """Raises the input to the power of 3."""
    return Density(vt.cube(df.AST))


@macro
def pow(base: AnyDensity, exponent: AnyDensity) -> Density[vt.pow]:
    if env.datapack_version < 113:
        if not isinstance(exponent, int):
            raise ValueError("Can only raise to integer powers in this version")
        if 0 <= abs(exponent) <= 3:
            result = {
                0: Density(vt.constant(1)),
                1: base,
                2: Density(vt.square(base.AST)),
                3: Density(vt.cube(base.AST))
            }[exponent]
        else:
            result = base
            for _ in range(abs(exponent) - 1):
                result = Density(vt.mul(result.AST, base.AST))
        if exponent < 0:
            result = Density(vt.reciprocal(result.AST))
        return result
    
    return Density(vt.pow(base.AST, exponent.AST))


@macro
def sum(*dfs: AnyDensity) -> Density[vt.add]:
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
def prod(*dfs: AnyDensity) -> Density[vt.mul]:
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
def clamp(input: AnyDensity, min: float, max: float) -> Density[vt.clamp]:
    """Returns the larger value from the input and min, and the smaller value from that and max."""
    return Density(vt.clamp(input.AST, min, max))


@macro
def min(*dfs: AnyDensity) -> Density[vt.min]:
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
def max(*dfs: AnyDensity) -> Density[vt.max]:
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
        diff_clamped = max(smoothing_factor - abs(result - x), 0.0)
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
        diff_clamped = max(smoothing_factor - abs(result - x), 0.0)
        power = diff_clamped**degree
        denominator = (2 * degree) * (smoothing_factor ** (degree - 1))

        result = min(result, x) - (power / denominator)

    return result


# ======// Rounding //============================================================================//


@macro
def round(df: AnyDensity, decimals: int = 0) -> Density[vt.round]:
    """Rounds the input to the nearest integer or given decimal."""
    if env.datapack_version is not None and env.datapack_version < 111:
        if decimals:
            return (
                (df * 10**decimals)
                + constant(1.5) * constant(2**52)
                - constant(1.5) * constant(2**52)
            ) / 10**decimals
        return (
            df + constant(1.5) * constant(2**52) - constant(1.5) * constant(2**52)
        )
    else:
        return Density(vt.round(df.AST, 10**-decimals))


@macro
def floor(df: AnyDensity, decimals: int = 0) -> Density[vt.floor]:
    """Rounds the input down to the nearest integer or given decimal."""
    if env.datapack_version is not None and env.datapack_version < 111:
        if decimals:
            return round((df - 0.5) * 10**decimals) / 10**decimals
        return round(df - 0.5)
    else:
        return Density(vt.floor(df.AST, 10**-decimals))


@macro
def ceil(df: AnyDensity, decimals: int = 0) -> Density[vt.ceil]:
    """Rounds the input up to the nearest integer or given decimal."""
    if env.datapack_version is not None and env.datapack_version < 111:
        if decimals:
            return round((df + 0.5) * 10**decimals) / 10**decimals
        return round(df + 0.5)
    else:
        return Density(vt.ceil(df.AST, 10**-decimals))


# TODO: Versionspezifizierung im decorator wieder entfernen?
@macro((111, NotImplemented))
def truncate(df: AnyDensity, decimals: int = 0) -> Density[vt.truncate]:
    """Truncates the input to the nearest integer or given decimal."""
    return Density(vt.truncate(df.AST, 10**-decimals))


@macro
def floordiv(dividend: AnyDensity, divisor: AnyDensity) -> Density[vt.floor]:
    """Returns the floor division of two inputs (`argument1 // argument2`)."""
    return floor(dividend / divisor)


@macro
def mod(dividend: AnyDensity, divisor: AnyDensity) -> Density[vt.sub]:
    """Returns the modulo of two inputs (`argument1 % argument2`)."""
    return caching.specified_cache(
        dividend - divisor * floor(dividend / divisor), dividend, divisor
    )


# ======// Step Functions //======================================================================//


@macro
def sgn(df: AnyDensity) -> Density[vt.range_choice]:
    """Returns `1.0` when the input is positive, `-1.0` when it's negative and itself when it's `0.0`."""
    if env.datapack_version is not None and env.datapack_version < 113:
        return (
            cond.when(df)
            .equals(0.0)
            .then(0.0)
            .elsewhen(cond.it)
            .less(0.0)
            .then(-1.0)
            .otherwise(1.0)
        )
    return Density(vt.sign(df.AST))


@macro
def heaviside(
    df: AnyDensity, *, at_zero: AnyDensity = 0.5
) -> Density[vt.range_choice]:
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
def ramp(df: AnyDensity) -> Density[vt.max]:
    """Returns the ramp function value of the input, meaning `argument1` itself, when it's positive, otherwise returns `0.0`."""
    return max(df, 0)


# ======// Spline //=============================================================================//


@macro
def spline(
    coordinate: AnyDensity, points: list[tuple[float, AnyDensity, float]]
) -> Density[vt.spline]:
    """Computes the value of a cubic spline for the input.

    The values for the points represent in order: `location`, `value` and `derivative`.

    For values beyond the outermost spline points, the value of the nearest spline point is returned.

    **NOTE:** If multiple spline points have the same location, for inputs less than the
    location, values aproaching the first defined value will be returned. For
    inputs equal to or greather than the location, values leaving the second
    defined values will be returned. ("first" and "second" refer to the order
    of definition in `points`).

    **NOTE:** Approximations for various functions done by splines can be found in `rhombus.macros.smath`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#spline) • [Wikipedia](https://en.wikipedia.org/wiki/Cubic_Hermite_spline)
    """
    points = [(p[0], p[1].AST, p[2]) for p in points]
    return Density(vt.spline(coordinate.AST, points))