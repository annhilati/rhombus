"""
`emath` stands for '*expensive* maths'. This is because the macros in this
module use approximation methods that have high cachingormance costs.
Either they require a large number of calculations, or they multiply
the abstract syntax tree of the input.

These methods typically include infinite series, such as Taylor series, or
iterative methods, such as Newton's method.
"""

from typing import Callable
import math as py_math

from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro
from rhombus.std import math, caching, conditional as cond
from rhombus.support import vanilla as vt


# ======// Rounding //============================================================================//


@macro
def round(
    df: AnyDensity, *, range: tuple[int, int] = (-1, 1)
) -> Density:
    """Rounds the input to the nearest integer within the specified range.
    Values outside this range's rounding intervals will be left unrounded."""
    start_int = py_math.ceil(range[0])
    end_int = py_math.floor(range[1])

    if start_int > end_int:
        raise ValueError("'range' requires a lower and upper bound")

    expr = (
        cond.when(df)
        .inside(start_int - 0.5, start_int + 0.5)
        .then(float(start_int))
    )

    i = start_int + 1
    while i <= end_int:
        expr = expr.elsewhen(cond.it).inside(i - 0.5, i + 0.5).then(float(i))
        i += 1

    return expr.otherwise(cond.it)


@macro
def floor(
    df: AnyDensity, *, range: tuple[int, int] = (-1, 1)
) -> Density:
    """Rounds the input down to the nearest integer within the specified range.
    Values outside this range's rounding intervals will be left unrounded."""
    from rhombus.core import environment

    EPS = environment.env.infinitesimal

    start_int = py_math.floor(range[0])
    end_int = py_math.floor(range[1])

    if start_int > end_int:
        raise ValueError("'range' requires a lower and upper bound")

    expr = (
        cond.when(df)
        .inside(start_int, start_int + 1.0 - EPS)
        .then(float(start_int))
    )

    i = start_int + 1
    while i <= end_int:
        expr = expr.elsewhen(cond.it).inside(i, i + 1.0 - EPS).then(float(i))
        i += 1

    return expr.otherwise(cond.it)


@macro
def ceil(
    df: AnyDensity, *, range: tuple[int, int] = (-1, 1)
) -> Density:
    """Rounds the input up to the nearest integer within the specified range.
    Values outside this range's rounding intervals will be left unrounded."""
    from rhombus.core import environment

    EPS = environment.env.infinitesimal

    start_int = py_math.ceil(range[0])
    end_int = py_math.ceil(range[1])

    if start_int > end_int:
        raise ValueError("'range' requires a lower and upper bound")

    expr = (
        cond.when(df)
        .inside(start_int - 1.0 + EPS, start_int)
        .then(float(start_int))
    )

    i = start_int + 1
    while i <= end_int:
        expr = expr.elsewhen(cond.it).inside(i - 1.0 + EPS, i).then(float(i))
        i += 1

    return expr.otherwise(cond.it)


# ======// Arithmetic //==========================================================================//


@macro
def floordiv(
    dividend: AnyDensity, divisor: AnyDensity, *, range: tuple[int, int] = (-1, 1)
) -> Density:
    """Returns the floor division of two inputs (`argument1 // argument2`) within the specified range.
    Values where the quotient falls outside this range's rounding intervals will be left unrounded."""
    return floor(dividend / divisor, range=range)


@macro
def mod(
    dividend: AnyDensity, divisor: AnyDensity, *, range: tuple[int, int] = (-1, 1)
) -> Density:
    """Returns the modulo of two inputs (`argument1 % argument2`) within the specified range.
    Values where the quotient falls outside this range's rounding intervals will not be calculated as true modulo."""
    return caching.recurrence_cache(
        dividend - divisor * floor(dividend / divisor, range=range)
    )


@macro
def sqrt(
    df: AnyDensity,
    iterations: int = 3,
    guess: Callable[[Density], Density] = lambda d: d * 0.5,
) -> Density:
    """Returns the square root of the input."""
    x = guess(df)

    for _ in range(iterations):
        x = 0.5 * (x + (df / x))

    return cond.when(df).atleast(0).then(x).otherwise(math.NaN)


@macro
def exp(df: AnyDensity, terms: int = 4) -> Density:
    """Returns the exponential function value of the input, so `e` exponentiated to the input."""
    if terms <= 0:
        return Density(1)

    terms_list = [Density(1)] + [
        (df**k) / py_math.factorial(k) for k in range(1, terms + 1)
    ]
    return math.sum(*terms_list)


@macro
def ln(df: AnyDensity, terms: int = 4) -> Density:
    """Returns the natual logarithm value of the input.<br>"""
    y = df - Density(1)

    terms_list = [
        ((-1 if (k % 2 == 0) else 1) * (y**k) / k) for k in range(1, terms + 1)
    ]
    return (
        cond.when(df).greater(0).then(math.sum(*terms_list)).otherwise(math.NaN)
    )