from density.language.density import Density
from density.language.functions import *
from density.language.functions import _interpret_args

def sign(argument: Density | float | str):
    argument = _interpret_args(argument)[0]
    return argument / abs(argument)