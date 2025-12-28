from rhombus.core.df_types import MAX_REASONABLE_VALUE, MIN_REASONABLE_VALUE
from rhombus.language.density import Density
from rhombus.language.functions import _arg_unwrapper
from rhombus.language import functions as f

def sign(argument: Density | float | str):
    """Returns `-1` when the input is negative, `1` when it is positive and `0` if it is `0`.
    
    This makro works by using `range_choice` logic. For an alternative see `sign2`.
    """
    
    argument = _arg_unwrapper(argument)
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

def sign2(argument: Density | float | str):
    """Returns `-1` when the input is negative, `1` when it is positive and `0` if it is `0`.
    
    ⚠️ This is suspected to not work properly. See [rhombus#6](https://github.com/annhilati/rhombus/issues/6).

    This makro works by using arithmetic. For an alternative see `sign`.
    """
    argument = Density(_arg_unwrapper(argument))
    return argument / abs(argument)