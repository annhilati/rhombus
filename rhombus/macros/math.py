from rhombus import config as cfg
from rhombus.std import Density, AnyDensity, functions as f, macro, vdft as vdft

pi = 3.1415926535897932 #38462643383279502884197169399375105820974944592307816406
"The constant `π` to 16 decimals."
e  = 2.7182818284590452 #35360287471352662497757247093699959574966
"Euler's number `e` to 16 decimals."


@macro
def linsqrt01(argument: AnyDensity) -> Density[vdft.add]:
    return 0.41731 + 0.59016*argument

@macro
def ratsqrt01(argument: AnyDensity) -> Density[vdft.mul]:
    return argument / (0.41731+0.59016*argument)


#======// Number Theory //=======================================================================//

@macro
def heaviside(argument: AnyDensity) -> Density[vdft.range_choice]:
    """Returns the Heaviside function value of the input which is `0.0` when the input is negative and `1.0` when it is positive.<br>

    **NOTE** This implementation uses a definition where `heaviside(0) = 0.5`.

    ---
    ⚙️ Implementation utilizes `range_choice` ┃ `CC(·) = 2 × CC(argument) + 5`
    """
    return f.range_choice(
        input=argument,
        min_inclusive=0,
        max_exclusive=cfg.infinitesimal,
        when_in_range=0.5,
        when_out_of_range=f.range_choice(
            input=argument,
            min_inclusive=-vdft.constant_number_limit,
            max_exclusive=0,
            when_in_range=0,
            when_out_of_range=1.0
        ))

@macro
def ramp(argument: AnyDensity) -> Density[vdft.max]:
    """Returns the ramp function value of the input, meaning `argument1` itself, when it's positive, otherwise returns `0.0`."""
    return f.max(argument, 0)

@macro
def sgn(argument: AnyDensity) -> Density[vdft.range_choice]:
    """Returns `1.0` when the input is positive, `-1.0` when it's negative and itself when it's `0.0`<br>

    ⚙️ This implementation uses `range_choice`.
    """
    return f.range_choice(
        input=argument,
        min_inclusive=0,
        max_exclusive=cfg.infinitesimal,
        when_in_range=0,
        when_out_of_range=f.range_choice(
            input=argument,
            min_inclusive=-vdft.constant_number_limit,
            max_exclusive=0,
            when_in_range=-1.0,
            when_out_of_range=1.0
        ))


#======// Arithmetic //==========================================================================//

@macro
def monus(argument1: AnyDensity, argument2: AnyDensity):
    """Returns `argument1 - argument2`, but when that's negative, returns `0.0` instead."""
    return f.max(argument1 - argument2, 0.0)

@macro
def sum(*arguments: AnyDensity) -> Density[vdft.add]:
    "Returns the sum of any number of arguments."
    if len(arguments) == 1:
        return arguments[0]
    
    it = iter(arguments)
    result = next(it) + next(it)

    for x in it:
        result = result + x

    return result

@macro
def prod(*arguments: AnyDensity) -> Density[vdft.mul]:
    "Returns the product of any number of arguments."
    if len(arguments) == 1:
        return arguments[0]
    
    it = iter(arguments)
    result = next(it) * next(it)

    for x in it:
        result = result * x

    return result