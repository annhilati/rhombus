from rhombus.core import df_types as dft 
from rhombus.language.density import Density, resolve_shorthands
from rhombus.language.builtins import MAX_REASONABLE_VALUE, MIN_REASONABLE_VALUE
from rhombus.language import builtins as f
from typing import Callable, Any

pi = 3.14159265359
e = 2.71828182846

def sgn(argument: Density | float | str):
    argument, = resolve_shorthands(argument)
    return argument / abs(argument)

def sgn2(argument: Density | float | str):
    argument, = resolve_shorthands(argument)
    return f.range_choice(
        input=argument,
        min_inclusive=0,
        max_exclusive=1/MAX_REASONABLE_VALUE,
        when_in_range=0,
        when_out_of_range=f.range_choice(
            input=argument,
            min_inclusive=MIN_REASONABLE_VALUE,
            max_exclusive=0,
            when_in_range=-1.0,
            when_out_of_range=1.0
        ))

def sqrt(argument: Density | float | str, iterations: int = 3, guess: Callable[[Density], Density] = lambda d: d / 2 + 0.5) -> Density[dft.mul]:
    """Returns the square root of the input.

    This makro uses [Heron's method](https://en.wikipedia.org/wiki/Square_root_algorithms#Heron's_method).
    
    <br>
    ```
    Iterations │ Decimals  │ Calculations
    ═══════════╪═══════════╪═════════════
    1          │ 1 – 2     │ 10
    2          │ 2 – 4     │ 24
    3          │ 4 – 8     │ 52
    4          │ 8 – 16    │ 108
    i          │ 2ⁱ⁻¹ – 2ⁱ │ 7 × 2ⁱ - 4
    ```
    """
    argument, = resolve_shorthands(argument)

    x = guess(argument)

    for _ in range(iterations):
        x = 0.5 * (x + (argument / x))

    return x

def heaviside(argument: Density | float | str):
    argument, = resolve_shorthands(argument)

    return 0.5 * (sgn(argument) + 1)

def monus(argument1: Density | float | str, argument2: Density | float | str):
    """Returns `argument1 - argument2`, but when its negative, returns `0.0` instead."""
    argument1, argument2 = resolve_shorthands(argument1, argument2)

    return f.max(Density(argument1) - Density(argument2), 0.0)