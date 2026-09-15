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


# ======// Arithmetic //==========================================================================//

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