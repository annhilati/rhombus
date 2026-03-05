"Macros with mathmatical functions, that are not provided by default."

from typing import Callable
from Rhombus import config as cfg
from Rhombus.language import dft as dft
from Rhombus.language.density import Density, DensityDescriptor, MacroWizard
from Rhombus.language import functions as f

pi = 3.1415926535897932 #38462643383279502884197169399375105820974944592307816406
"The constant `π` to 16 decimals."
e  = 2.7182818284590452 #35360287471352662497757247093699959574966
"Euler's number `e` to 16 decimals."



@MacroWizard
def linsqrt01(argument: DensityDescriptor) -> Density[dft.add]:
    return 0.41731 + 0.59016*argument

@MacroWizard
def ratsqrt01(argument: DensityDescriptor) -> Density[dft.mul]:
    return argument / (0.41731+0.59016*argument)


#======// Number Theory //=======================================================================//

@MacroWizard
def heaviside(argument: DensityDescriptor) -> Density[dft.range_choice]:
    """Returns the Heaviside function value of the input which is `0.0` when the input is negative and `1.0` when it is positive.<br>

    **NOTE** This implementation uses a definition where `heaviside(0) = 0.5`.

    ---
    ⚙️ Implementation utilizes `range_choice` ┃ `CC(·) = 2 × CC(argument) + 5`
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

@MacroWizard
def ramp(argument: DensityDescriptor) -> Density[dft.max]:
    """Returns the ramp function value of the input, meaning `argument1` itself, when it's positive, otherwise returns `0.0`."""
    return f.max(argument, 0)

@MacroWizard
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


#======// Arithmetic //==========================================================================//

@MacroWizard
def monus(argument1: DensityDescriptor, argument2: DensityDescriptor):
    """Returns `argument1 - argument2`, but when that's negative, returns `0.0` instead."""
    return f.max(argument1 - argument2, 0.0)

@MacroWizard
def sum(*arguments: DensityDescriptor) -> Density[dft.add]:
    "Returns the sum of any number of arguments."
    if len(arguments) == 1:
        return arguments[0]
    
    it = iter(arguments)
    result = next(it) + next(it)

    for x in it:
        result = result + x

    return result

@MacroWizard
def prod(*arguments: DensityDescriptor) -> Density[dft.mul]:
    "Returns the product of any number of arguments."
    if len(arguments) == 1:
        return arguments[0]
    
    it = iter(arguments)
    result = next(it) * next(it)

    for x in it:
        result = result * x

    return result



@MacroWizard
def symsmoothstep(argument: DensityDescriptor) -> Density[dft.add]:
    # [-1,1] -> [-1,1]
    return f.spline(
        argument,
        [
            (-1, -1, 0),
            ( 1,  1, 0)
        ]
    )