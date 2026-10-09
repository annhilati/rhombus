"""
The macros in this
module use approximation methods that have high performance costs.
Either they require a large number of calculations, or they multiply
the abstract syntax tree of the input.

These methods typically include infinite series, such as Taylor series, or
iterative methods, such as Newton's method.
"""

from typing import Callable
import math as py_math

from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro
from rhombus.std import math, caching


@macro
def sqrt(
    df: AnyDensity,
    iterations: int = 3,
    guess: Callable[[Density], Density] = lambda d: d * 0.5,
) -> Density:
    """Approximates the square root of the input."""
    if iterations < 1:
            raise ValueError("Need one iteration at least")
    
    x = guess(df)

    for _ in range(iterations):
        x = 0.5 * (x + (df / x))

    return caching.new_cache_transformer(x if df >= 0 else math.NaN, targets=(df))


@macro
def exp(df: AnyDensity, terms: int = 4) -> Density:
    """Approximates the value of the input on the exponential function."""
    if terms < 1:
        raise ValueError("Need one term at least")

    return caching.new_cache_transformer(math.sum(Density(1), *(
        (df**k) / py_math.factorial(k) for k in range(1, terms + 1)
    )), targets=(df))


@macro
def ln(df: AnyDensity, terms: int = 4) -> Density:
    """Approximates the value of the input on the natual logarithm."""
    if terms < 1:
            raise ValueError("Need one term at least")

    return caching.new_cache_transformer(math.sum(*(
        ((-1 if (k % 2 == 0) else 1) * ((df - 1)**k) / k) for k in range(1, terms + 1)
    )) if df > 0 else math.NaN, targets=(df))