from rhombus.core import df_types as dft 
from rhombus.language.density import Density, resolve_shorthands
from rhombus.language.builtins import MAX_REASONABLE_VALUE, MIN_REASONABLE_VALUE
from rhombus.language import builtins as f
from typing import Callable

pi = 3.14159265359
e = 2.71828182846

def heaviside(argument: Density | float | str):
    """Returns the Heaviside function value of the input which is `0.0` when the input is negative and `1.0` when it is positive.<br>
    ❗`heaviside(0) = NaN`
    """
    argument, = resolve_shorthands(argument)
    return 0.5 * (sgn(argument) + 1)

def monus(argument1: Density | float | str, argument2: Density | float | str):
    """Returns `argument1 - argument2`, but when that's negative, returns `0.0` instead."""
    arg1, arg2 = resolve_shorthands(argument1, argument2)
    return f.max(Density(arg1) - Density(arg2), 0.0)

def ramp(argument: Density | float | str):
    """Returns the ramp function value of the input, meaning `argument1` itself, when it's positive, otherwise returns `0.0`."""
    arg, = resolve_shorthands(argument)
    return f.max(arg, 0)

def sgn(argument: Density | float | str):
    """Returns `1.0` when the input is positive and `-1.0` when it's negative.<br>
    ❗`sgn(0) = NaN`

    ⚙️ This implementation uses arithmetic. For an alternative, see `sgn_ranged()`.
    """
    arg, = resolve_shorthands(argument)
    return abs(arg) / arg

def sgn_ranged(argument: Density | float | str):
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

def sqrt(argument: Density | float | str, iterations: int = 3, guess: Callable[[Density], Density] = lambda d: d * 0.5) -> Density[dft.mul]:
    """Returns the square root of the input.<br>

    ⚙️ This implementation uses [Heron's method](https://en.wikipedia.org/wiki/Square_root_algorithms#Heron's_method).
    
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