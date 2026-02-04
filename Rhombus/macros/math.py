"Macros with mathmatical functions, that are not provided by default."

from typing import Callable
from Rhombus.core import df_types as dft, config as cfg
from Rhombus.language.density import Density, DensityDescriptor, MacroAssistant
from Rhombus.language import builtins as f

pi = 3.14159265359
"The constant π to 11 decimals."
e = 2.71828182846
"Euler's number e to 10 decimals."


#======// Number Theory //=======================================================================//

@MacroAssistant
def heaviside(argument: DensityDescriptor) -> Density[dft.range_choice]:
    """Returns the Heaviside function value of the input which is `0.0` when the input is negative and `1.0` when it is positive.<br>
    ❗`heaviside(0) = 0.5`

    ⚙️ This implementation uses `range_choice`.
    """
    return f.range_choice(
        input=argument,
        min_inclusive=0,
        max_exclusive=1/cfg.constant_number_limit,
        when_in_range=0.5,
        when_out_of_range=f.range_choice(
            input=argument,
            min_inclusive=-cfg.constant_number_limit,
            max_exclusive=0,
            when_in_range=0,
            when_out_of_range=1.0
        ))

@MacroAssistant
def ramp(argument: DensityDescriptor) -> Density[dft.max]:
    """Returns the ramp function value of the input, meaning `argument1` itself, when it's positive, otherwise returns `0.0`."""
    return f.max(argument, 0)

@MacroAssistant
def sgn(argument: DensityDescriptor) -> Density[dft.range_choice]:
    """Returns `1.0` when the input is positive, `-1.0` when it's negative and itself when it's `0.0`<br>

    ⚙️ This implementation uses `range_choice`.
    """
    return f.range_choice(
        input=argument,
        min_inclusive=0,
        max_exclusive=1/cfg.constant_number_limit,
        when_in_range=0,
        when_out_of_range=f.range_choice(
            input=argument,
            min_inclusive=-cfg.constant_number_limit,
            max_exclusive=0,
            when_in_range=-1.0,
            when_out_of_range=1.0
        ))

@MacroAssistant
def sqrt(argument: DensityDescriptor, iterations: int = 3, guess: Callable[[Density], Density] = lambda d: d * 0.5) -> Density[dft.mul]:
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

@MacroAssistant
def exp(argument: DensityDescriptor, terms: int = 4) -> Density[dft.add]:
    """Returns `e` exponentiated to the input.<br>

    ⚙️ This implementation uses the [Taylor series of the exponential function](https://en.wikipedia.org/wiki/Taylor_series#Exponential_function).<br>
    """
    from math import factorial

    result = f.constant(1)
    for k in range(1, terms + 1):
        term = (argument ** k) / factorial(k)
        result += term

    return result

@MacroAssistant
def ln(argument: DensityDescriptor, terms: int = 4) -> Density[dft.add]:
    """Returns the natual logarithm value of the input.<br>

    ⚙️ This implementation uses the [Taylor series of the natural logarithm](https://en.wikipedia.org/wiki/Taylor_series#Natural_logarithm).<br>
    """
    y = argument - f.constant(1)

    result = f.constant(0)
    for k in range(1, terms + 1):
        coeff = -1 if (k % 2 == 0) else 1
        term = coeff * (y ** k) / k
        result += term

    return result

#======// Arithmetic //==========================================================================//

@MacroAssistant
def monus(argument1: DensityDescriptor, argument2: DensityDescriptor):
    """Returns `argument1 - argument2`, but when that's negative, returns `0.0` instead."""
    return f.max(argument1 - argument2, 0.0)

@MacroAssistant
def sum(*arguments: DensityDescriptor) -> Density[dft.add]:
    "Returns the sum of any number of arguments."
    if len(arguments) == 1:
        return arguments[0]
    
    it = iter(arguments)
    result = next(it) + next(it)

    for x in it:
        result = result + x

    return result

@MacroAssistant
def prod(*arguments: DensityDescriptor) -> Density[dft.mul]:
    "Returns the product of any number of arguments."
    if len(arguments) == 1:
        return arguments[0]
    
    it = iter(arguments)
    result = next(it) * next(it)

    for x in it:
        result = result * x

    return result


#======// Trigonometry //========================================================================//

@MacroAssistant
def sin(argument: DensityDescriptor, terms: int = 3) -> Density[dft.add]:
    """Returns the sine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of sine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    from math import factorial

    result = argument
    for k in range(1, terms + 1):
        power = 2 * k + 1
        coeff = -1 if (k % 2) else 1
        term = coeff * (argument ** power) / factorial(power)
        result += term

    return result

@MacroAssistant
def cos(argument: DensityDescriptor, terms: int = 3) -> Density[dft.add]:
    """Returns the cosine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of cosine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    from math import factorial

    result = f.constant(1)
    for k in range(1, terms + 1):
        power = 2 * k
        coeff = -1 if (k % 2) else 1
        term = coeff * (argument ** power) / factorial(power)
        result += term

    return result

@MacroAssistant
def tan(argument: DensityDescriptor, terms: int = 3) -> Density[dft.mul]:
    """Returns the tangent value of the input in radians.<br>
    ❗`tan((2n - 1) * x) = NaN` where `x` is near π/2.

    ⚙️ This implementation uses the [Taylor series of sine and cosine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """

    return sin(argument, terms) / cos(argument, terms)

@MacroAssistant
def asin(argument: DensityDescriptor, terms: int = 3) -> Density[dft.add]:
    """Returns the arc sine value of the input in radians.<br>
    ❗`asin(x) = NaN`, if `x < -1` or `x > 1`

    ⚙️ This implementation uses the [Taylor series of arc sine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    """
    from math import factorial

    result = f.constant(0)
    for k in range(terms):
        coeff = factorial(2*k) / (4**k * factorial(k)**2 * (2*k + 1))
        term = coeff * (argument ** (2*k + 1))
        result = result + term

    return result

@MacroAssistant
def acos(argument: DensityDescriptor, terms: int = 3) -> Density[dft.add]:
    """Returns the arc cosine value of the input in radians.<br>
    ❗`acos(x) = NaN`, if `x < -1` or `x > 1`

    ⚙️ This implementation uses the shifted [Taylor series of arc sine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    """
    return (pi / 2) - asin(argument, terms)

@MacroAssistant
def atan(argument: DensityDescriptor, terms: int = 3) -> Density[dft.add]:
    """Returns the arc tangent value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of arc tangent](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    result = f.constant(0)
    for k in range(terms):
        coeff = -1 if (k % 2) else 1
        term = coeff * (argument ** (2*k + 1)) / (2*k + 1)
        result = result + term

    return result

@MacroAssistant
def sinh(argument: DensityDescriptor, terms: int = 3) -> Density[dft.add]:
    """Returns the hyperbolic sine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of hyperbolic sine](https://en.wikipedia.org/wiki/Taylor_series#Hyperbolic_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    from math import factorial

    result = f.constant(0)
    for k in range(terms):
        power = 2*k + 1
        term = (argument ** power) / factorial(power)
        result = result + term

    return result

@MacroAssistant
def cosh(argument: DensityDescriptor, terms: int = 3) -> Density[dft.add]:
    """Returns the hyperbolic cosine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of hyperbolic cosine](https://en.wikipedia.org/wiki/Taylor_series#Hyperbolic_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    from math import factorial

    result = f.constant(1)
    for k in range(1, terms + 1):
        power = 2*k
        term = (argument ** power) / factorial(power)
        result = result + term

    return result
