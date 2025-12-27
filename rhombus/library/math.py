from rhombus.language.density import Density
from rhombus.language.functions import *
from rhombus.language.functions import _interpret_args
from rhombus.core.df_types import MAX_REASONABLE_VALUE, MIN_REASONABLE_VALUE

def sign(argument: Density | float | str):
    "Returns `-1` when the input is negative, `1` when it is positive and `0` if it is neither."
    argument = _interpret_args(argument)[0]
    return range_choice(
        input=argument,
        max_exclusive=0,
        min_inclusive=0,
        when_in_range=0,
        when_out_of_range=range_choice(
            input=argument,
            max_exclusive=0,
            min_inclusive=MIN_REASONABLE_VALUE,
            when_in_range=-1.0,
            when_out_of_range=1.0
        ))
    # Whether the following would work too is currently unknown, because invert seems to return a constant
    # return argument / abs(argument)