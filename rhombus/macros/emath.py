"""
`emath` stands for '*expensive* maths'. This is because the macros in this
module use approximation methods that have high performance costs.
Either they require a large number of calculations, or they multiply
the abstract syntax tree of the input.

These methods typically include infinite series, such as Taylor series, or iterative methods, such as Newton's method.
"""

from typing import Callable
from rhombus.std.density import Density, AnyDensity
from rhombus.std import functions, macro, types
from rhombus.macros.math import pi, sum as msum

__all__ = []


@macro
def sqrt(argument: AnyDensity, iterations: int = 3, guess: Callable[[Density], Density] = lambda d: d * 0.5) -> Density[types.mul]:
    """Returns the square root of the input.<br>
    ❗`sqrt(x)` is nonesense, if `x < 0`

    ⚙️ This implementation uses [Heron's method](https://en.wikipedia.org/wiki/Square_root_algorithms#Heron's_method).<br>
    ⚠️ Bigger inputs need more iterations before converging.
    
    #### Precision for reasonable small inputs`
    ```
    Iterations │ Decimals  │ Calculations
    ═══════════╪═══════════╪══════════════════════════════
    1          │ 1 – 2     │
    2          │ 2 – 4     │      2ⁱ × c(guess)
    3          │ 4 – 8     │            +
    4          │ 8 – 16    │ (2ⁱ - 1) × (c(argument) + 3)
    i          │ 2ⁱ⁻¹ – 2ⁱ │
    ```
    """
    x = guess(argument)

    for _ in range(iterations):
        x = 0.5 * (x + (argument / x))

    return x

@macro
def exp(argument: AnyDensity, terms: int = 4) -> Density[types.add]:
    """Returns the exponential function value of the input, so `e` exponentiated to the input.<br>

    ⚙️ This implementation uses the [Taylor series of the exponential function](https://en.wikipedia.org/wiki/Taylor_series#Exponential_function).
    """
    from math import factorial

    if terms <= 0:
        return functions.constant(1)

    terms_list = [functions.constant(1)] + [ (argument ** k) / factorial(k) for k in range(1, terms + 1) ]
    return msum(*terms_list)

@macro
def ln(argument: AnyDensity, terms: int = 4) -> Density[types.add]:
    """Returns the natual logarithm value of the input.<br>

    ⚙️ This implementation uses the [Taylor series of the natural logarithm](https://en.wikipedia.org/wiki/Taylor_series#Natural_logarithm).
    """
    y = argument - functions.constant(1)

    if terms <= 0:
        return functions.constant(0)

    terms_list = [((-1 if (k % 2 == 0) else 1) * (y ** k) / k) for k in range(1, terms + 1)]
    return msum(*terms_list)

#======// Trigonometry //========================================================================//

@macro
def sin(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the sine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of sine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    from math import factorial

    terms_list = [argument] + [((-1 if (k % 2) else 1) * (argument ** (2 * k + 1)) / factorial(2 * k + 1)) for k in range(1, terms + 1)]
    return msum(*terms_list)

@macro
def cos(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the cosine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of cosine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    from math import factorial

    terms_list = [functions.constant(1)] + [((-1 if (k % 2) else 1) * (argument ** (2 * k)) / factorial(2 * k)) for k in range(1, terms + 1)]
    return msum(*terms_list)

@macro
def tan(argument: AnyDensity, terms: int = 3) -> Density[types.mul]:
    """Returns the tangent value of the input in radians.<br>
    ❗`tan((2n - 1) * x) = NaN` where `x` is near π/2.

    ⚙️ This implementation uses the [Taylor series of sine and cosine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """

    return sin(argument, terms) / cos(argument, terms)

@macro
def asin(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the arc sine value of the input in radians.<br>
    ❗`asin(x) = NaN`, if `x < -1` or `x > 1`

    ⚙️ This implementation uses the [Taylor series of arc sine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    """
    from math import factorial

    if terms <= 0:
        return functions.constant(0)

    terms_list = [(factorial(2*k) / (4**k * factorial(k)**2 * (2*k + 1))) * (argument ** (2*k + 1)) for k in range(terms)]
    return msum(*terms_list)

@macro
def acos(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the arc cosine value of the input in radians.<br>
    ❗`acos(x) = NaN`, if `x < -1` or `x > 1`

    ⚙️ This implementation uses the shifted [Taylor series of arc sine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    """
    return (pi / 2) - asin(argument, terms)

@macro
def atan(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the arc tangent value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of arc tangent](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    if terms <= 0:
        return functions.constant(0)

    terms_list = [((-1 if (k % 2) else 1) * (argument ** (2*k + 1)) / (2*k + 1)) for k in range(terms)]
    return msum(*terms_list)

@macro
def sinh(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the hyperbolic sine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of hyperbolic sine](https://en.wikipedia.org/wiki/Taylor_series#Hyperbolic_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    from math import factorial

    if terms <= 0:
        return functions.constant(0)

    terms_list = [ (argument ** (2*k + 1)) / factorial(2*k + 1) for k in range(terms) ]
    return msum(*terms_list)

@macro
def cosh(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the hyperbolic cosine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of hyperbolic cosine](https://en.wikipedia.org/wiki/Taylor_series#Hyperbolic_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    from math import factorial

    terms_list = [functions.constant(1)] + [ (argument ** (2*k)) / factorial(2*k) for k in range(1, terms + 1) ]
    return msum(*terms_list)