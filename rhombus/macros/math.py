"Macros with mathmatical functions, that are not provided by default."

from rhombus.core import df_types as dft 
from rhombus.language.density import Density, resolve_shorthands, DensityDescriptor
from rhombus.language.builtins import MAX_REASONABLE_VALUE, MIN_REASONABLE_VALUE
from rhombus.language import builtins as f
from typing import Callable

pi = 3.14159265359
e = 2.71828182846

def heaviside(argument: DensityDescriptor):
    """Returns the Heaviside function value of the input which is `0.0` when the input is negative and `1.0` when it is positive.<br>
    ❗`heaviside(0) = NaN`
    """
    arg, = resolve_shorthands(argument)
    return 0.5 * (sgn(arg) + 1)

def monus(argument1: DensityDescriptor, argument2: DensityDescriptor):
    """Returns `argument1 - argument2`, but when that's negative, returns `0.0` instead."""
    arg1, arg2 = resolve_shorthands(argument1, argument2)
    return f.max(arg1 - arg2, 0.0)

def ramp(argument: DensityDescriptor):
    """Returns the ramp function value of the input, meaning `argument1` itself, when it's positive, otherwise returns `0.0`."""
    arg, = resolve_shorthands(argument)
    return f.max(arg, 0)

def sgn(argument: DensityDescriptor):
    """Returns `1.0` when the input is positive and `-1.0` when it's negative.<br>
    ❗`sgn(0) = NaN`

    ⚙️ This implementation uses arithmetic. For an alternative, see `sgn_ranged()`.
    """
    arg, = resolve_shorthands(argument)
    return abs(arg) / arg

def sgn_ranged(argument: DensityDescriptor):
    """Returns `1.0` when the input is positive, `-1.0` when it's negative and itself when it's `0.0`<br>

    ⚙️ This implementation uses `range_choice`. For an alternative, see `sgn()`.
    """
    arg, = resolve_shorthands(argument)
    return f.range_choice(
        input=arg,
        min_inclusive=0,
        max_exclusive=1/MAX_REASONABLE_VALUE,
        when_in_range=0,
        when_out_of_range=f.range_choice(
            input=arg,
            min_inclusive=MIN_REASONABLE_VALUE,
            max_exclusive=0,
            when_in_range=-1.0,
            when_out_of_range=1.0
        ))

def sqrt(argument: DensityDescriptor, iterations: int = 3, guess: Callable[[Density], Density] = lambda d: d * 0.5) -> Density[dft.mul]:
    """Returns the square root of the input.<br>

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
    arg, = resolve_shorthands(argument)

    x = guess(arg)

    for _ in range(iterations):
        x = 0.5 * (x + (arg / x))

    return x

def sin(argument: DensityDescriptor, terms: int = 4) -> Density[dft.add]:
    """Returns the sine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of sine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.

    #### Precision for inputs between `1` and `-1`
    ```
    Terms  │ Decimals │ Calculations
    ═══════╪══════════╪══════════════════════════════
    1      │ 0        │
    2      │ 2        │ 
    3      │ 3        │ 
    4      │ 5        │ 
    5      │ 7        │ 
    ```
    
    """
    from math import factorial

    arg, = resolve_shorthands(argument)

    result = arg
    for k in range(1, terms + 1):
        power = 2 * k + 1
        coeff = -1 if (k % 2) else 1
        term = coeff * (arg ** power) / factorial(power)
        result += term

    return result

def cos(argument: DensityDescriptor, terms: int = 4) -> Density[dft.add]:
    """Returns the cosine value of the input in radians.<br>

    ⚙️ This implementation uses the [Taylor series of cosine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.

    #### Precision for inputs between `1` and `-1`
    ```
    Terms  │ Decimals │ Calculations
    ═══════╪══════════╪══════════════════════════════
    1      │ 0        │
    2      │ 2        │
    3      │ 4        │
    4      │ 6        │
    5      │ 8        │
    ```
    """
    from math import factorial

    arg, = resolve_shorthands(argument)

    result = f.constant(1)
    for k in range(1, terms + 1):
        power = 2 * k
        coeff = -1 if (k % 2) else 1
        term = coeff * (arg ** power) / factorial(power)
        result += term

    return result

def tan(argument: DensityDescriptor, terms: int = 4) -> Density[dft.mul]:
    """Returns the tangent value of the input in radians.<br>
    ❗`tan((2n - 1) * x) = NaN` where `x` is near π/2.

    ⚙️ This implementation uses the [Taylor series of sine and cosine](https://en.wikipedia.org/wiki/Taylor_series#Trigonometric_functions).<br>
    ⚠️ Bigger inputs need more terms before converging.
    """
    arg, = resolve_shorthands(argument)

    return sin(arg, terms) / cos(arg, terms)
