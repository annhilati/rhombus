"""
`emath` stands for '*expensive* maths'. This is because the macros in this
module use approximation methods that have high performance costs.
Either they require a large number of calculations, or they multiply
the abstract syntax tree of the input.

These methods typically include infinite series, such as Taylor series, or
iterative methods, such as Newton's method.
"""

from typing import Callable
import math as py_math

from rhombus.std.density import Density, AnyDensity
from rhombus.std import functions, macro, types
from rhombus.macros import math, conditional as cond, performance as perf


#======// Rounding //============================================================================//

@macro
def round(argument: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.range_choice]:
    """Rounds the input to the nearest integer within the specified range.
    Values outside this range's rounding intervals will be left unrounded."""
    start_int = py_math.ceil(range[0])
    end_int = py_math.floor(range[1])
    
    if start_int > end_int:
        raise ValueError("'range' requires a lower and upper bound")
        
    expr = cond.when(argument).inside(start_int - 0.5, start_int + 0.5).then(float(start_int))
    
    i = start_int + 1
    while i <= end_int:
        expr = expr.elsewhen(cond.it).inside(i - 0.5, i + 0.5).then(float(i))
        i += 1
        
    return expr.otherwise(cond.it)

@macro
def floor(argument: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.range_choice]:
    """Rounds the input down to the nearest integer within the specified range.
    Values outside this range's rounding intervals will be left unrounded."""
    from rhombus.core import config
    EPS = config.env.infinitesimal
    
    start_int = py_math.floor(range[0])
    end_int = py_math.floor(range[1])
    
    if start_int > end_int:
        raise ValueError("'range' requires a lower and upper bound")
        
    expr = cond.when(argument).inside(start_int, start_int + 1.0 - EPS).then(float(start_int))
    
    i = start_int + 1
    while i <= end_int:
        expr = expr.elsewhen(cond.it).inside(i, i + 1.0 - EPS).then(float(i))
        i += 1
        
    return expr.otherwise(cond.it)

@macro
def ceil(argument: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.range_choice]:
    """Rounds the input up to the nearest integer within the specified range.
    Values outside this range's rounding intervals will be left unrounded."""
    from rhombus.core import config
    EPS = config.env.infinitesimal
    
    start_int = py_math.ceil(range[0])
    end_int = py_math.ceil(range[1])
    
    if start_int > end_int:
        raise ValueError("'range' requires a lower and upper bound")
        
    expr = cond.when(argument).inside(start_int - 1.0 + EPS, start_int).then(float(start_int))
    
    i = start_int + 1
    while i <= end_int:
        expr = expr.elsewhen(cond.it).inside(i - 1.0 + EPS, i).then(float(i))
        i += 1
        
    return expr.otherwise(cond.it)


#======// Arithmetic //==========================================================================//

@macro
def floordiv(dividend: AnyDensity, divisor: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.range_choice]:
    """Returns the floor division of two inputs (`argument1 // argument2`) within the specified range.
    Values where the quotient falls outside this range's rounding intervals will be left unrounded."""
    return floor(dividend / divisor, range=range)

@macro
def mod(dividend: AnyDensity, divisor: AnyDensity, *, range: tuple[int, int] = (-1, 1)) -> Density[types.add]:
    """Returns the modulo of two inputs (`argument1 % argument2`) within the specified range.
    Values where the quotient falls outside this range's rounding intervals will not be calculated as true modulo."""
    return perf.autocache(dividend - divisor * floor(dividend / divisor, range=range))

@macro
def sqrt(argument: AnyDensity, iterations: int = 3, guess: Callable[[Density], Density] = lambda d: d * 0.5) -> Density[types.range_choice]:
    """Returns the square root of the input.
    """
    x = guess(argument)

    for _ in range(iterations):
        x = 0.5 * (x + (argument / x))

    return cond.when(argument).atleast(0).then(x).otherwise(math.NaN)

@macro
def exp(argument: AnyDensity, terms: int = 4) -> Density[types.add]:
    """Returns the exponential function value of the input, so `e` exponentiated to the input.
    """
    if terms <= 0:
        return functions.constant(1)

    terms_list = [functions.constant(1)] + [ (argument ** k) / py_math.factorial(k) for k in range(1, terms + 1) ]
    return math.sum(*terms_list)

@macro
def ln(argument: AnyDensity, terms: int = 4) -> Density[types.range_choice]:
    """Returns the natual logarithm value of the input.<br>
    """
    y = argument - functions.constant(1)

    terms_list = [((-1 if (k % 2 == 0) else 1) * (y ** k) / k) for k in range(1, terms + 1)]
    return cond.when(argument).greater(0).then(math.sum(*terms_list)).otherwise(math.NaN)


#======// Trigonometry //========================================================================//

@macro
def sin(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the sine value of the input in radians.
    """
    terms_list = [argument] + [((-1 if (k % 2) else 1) * (argument ** (2 * k + 1)) / py_math.factorial(2 * k + 1)) for k in range(1, terms + 1)]
    return math.sum(*terms_list)

@macro
def cos(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the cosine value of the input in radians.
    """
    terms_list = [functions.constant(1)] + [((-1 if (k % 2) else 1) * (argument ** (2 * k)) / py_math.factorial(2 * k)) for k in range(1, terms + 1)]
    return math.sum(*terms_list)

@macro
def tan(argument: AnyDensity, terms: int = 3) -> Density[types.mul]:
    """Returns the tangent value of the input in radians.
    """
    return sin(argument, terms) / cos(argument, terms)

@macro
def asin(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the arc sine value of the input in radians.
    """
    terms_list = [(py_math.factorial(2*k) / (4**k * py_math.factorial(k)**2 * (2*k + 1))) * (argument ** (2*k + 1)) for k in range(terms)]
    return cond.when(argument).inside(-1, 1).then(math.sum(*terms_list)).otherwise(math.NaN)

@macro
def acos(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the arc cosine value of the input in radians.
    """
    return cond.when(argument).inside(-1, 1).then((math.pi / 2) - asin(argument, terms)).otherwise(math.NaN)

@macro
def atan(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the arc tangent value of the input in radians.
    """
    terms_list = [((-1 if (k % 2) else 1) * (argument ** (2*k + 1)) / (2*k + 1)) for k in range(terms)]
    return math.sum(*terms_list)

@macro
def sinh(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the hyperbolic sine value of the input in radians.<br>
    """
    terms_list = [ (argument ** (2*k + 1)) / py_math.factorial(2*k + 1) for k in range(terms) ]
    return math.sum(*terms_list)

@macro
def cosh(argument: AnyDensity, terms: int = 3) -> Density[types.add]:
    """Returns the hyperbolic cosine value of the input in radians.<br>
    """
    terms_list = [functions.constant(1)] + [ (argument ** (2*k)) / py_math.factorial(2*k) for k in range(1, terms + 1) ]
    return math.sum(*terms_list)