"""The `smath` module features Hermite spline approximations of common mathematical functions.
"""

__all__ = [
    "atan", "cos", "coth", "normalCDF", "normalPDF", "sin", "smoothstep", "tan", "tanh", "erf", "logistic"
]

import math as py_math
from math import sqrt, pi

from rhombus.std import Density, AnyDensity, functions, types, macro
from rhombus import splines


@macro
def atan(argument: AnyDensity, xRange: tuple[float, float] = (-1, 1)) -> Density[types.spline]:
    """Evaluates the arc tangent value of the input.

    Parameters:
        xRange ((float, float)): The interval over which the function can take inputs.
    """
    return functions.spline(argument, splines.sample_spline_points(py_math.atan, xRange))

@macro
def cos(argument: AnyDensity, xRange: tuple[float, float] = (-pi, pi)) -> Density[types.spline]:
    """Evaluates the cosine value of the input.

    Parameters:
        xRange ((float, float)): The interval over which the function can take inputs.
            A wider interval will automatically use more spline points to maintain accuracy.
    """
    points = max(round(2 * (xRange[1] - xRange[0]) / pi + 1), 3)
    return functions.spline(argument, splines.sample_spline_points(py_math.cos, xRange, points))

@macro
def coth(argument: AnyDensity, xRange: tuple[float, float] = (-1, 1)) -> Density[types.spline]:
    """Evaluates the hyperbolic cotangent value of the input.

    Parameters:
        xRange ((float, float)): The interval over which the function can take inputs.
    """
    return 1 / tanh(argument, xRange)

@macro
def erf(argument: AnyDensity, xRange: tuple[float, float] = (-3, 3)) -> Density[types.spline]:
    """Evaluates the value of the input on Gaussian error function."""
    return functions.spline(argument, splines.sample_spline_points(py_math.erf, xRange))

@macro
def exp(argument: AnyDensity, xRange: tuple[float, float] = (-1, 1), base: float = py_math.e) -> Density[types.spline]:
    """Evaluates the value of the input on an exponential function."""
    func = lambda x: base**x
    return functions.spline(argument, splines.sample_spline_points(func, xRange))

@macro
def logistic(argument: AnyDensity,
        capacity: float = 1,
        growth_rate: float = 4,
        center: float = 0,
        xRange: tuple[float, float] = (-1, 1)
    ) -> Density[types.spline]:
    """Evaluates the value of the input on a logistic function.

    Parameters:
        capacity (float): 
        growth_rate (float): Controlls the steepness of the curve.
        center (float): The point around which the function is rotationally symmetric.
        xRange ((float, float)): The interval over which the function can take inputs.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Logistic_function)
    """
    func = lambda x: capacity / ( 1 + py_math.exp(- growth_rate * (x - center)))
    return functions.spline(argument, splines.sample_spline_points(func, xRange))

@macro
def normalPDF(argument: AnyDensity, mean: float = 0, standard_deviation: float = 1/sqrt(2 * pi)) -> Density[types.spline]:
    """Evaluates the value of the input on a normal distributed probability density function.

    Parameters:
        mean (float): The center of the normal distribution.
        standard_deviation (float): Controlls the spread or dispersion of the function relative to its mean.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Normal_distribution)
    """
    func = lambda x: (
        1/(standard_deviation * py_math.sqrt(2 * py_math.pi))
        * py_math.exp(-0.5 * ((x - mean) / standard_deviation) ** 2)
    )
    return functions.spline(argument, splines.sample_spline_points(func, (mean - 3.5*standard_deviation, mean + 3.5*standard_deviation), 13))

@macro
def normalCDF(argument: AnyDensity, mean: float = 0, standard_deviation: float = 1/sqrt(2 * pi)) -> Density[types.spline]:
    """Evaluates the value of the input on a normal distributed cumulative distribution function.

    Parameters:
        mean (float): The center of the normal distribution.
        standard_deviation (float): Controlls the spread or dispersion of the function relative to its mean.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Normal_distribution)
    """
    func = lambda x: 0.5 * (1 + py_math.erf((x - mean) / (standard_deviation * py_math.sqrt(2))))
    return functions.spline(argument, splines.sample_spline_points(func, (mean - 3.5*standard_deviation, mean + 3.5*standard_deviation), 13))

@macro
def sin(argument: AnyDensity, xRange: tuple[float, float] = (-pi, pi)) -> Density[types.spline]:
    """Evaluates the sine value of the input.

    Parameters:
        xRange ((float, float)): The interval over which the function can take inputs.
            A wider interval will automatically use more spline points to maintain accuracy.
    """
    points = max(round(2 * (xRange[1] - xRange[0]) / pi + 1), 3)
    return functions.spline(argument, splines.sample_spline_points(py_math.sin, xRange, points))

@macro
def smoothstep(argument: AnyDensity, xRange: tuple[float, float] = (-1, 1), yRange: tuple[float, float] = (-1, 1)) -> Density[types.spline]:
    """Evaluates a smoothstep transition of the input.

    The smoothstep curve rises smoothly from `yRange[0]` to `yRange[1]` while the
    input moves from `xRange[0]` to `xRange[1]`. Outside the latter interval the output
    is clamped to the respective boundary value.

    Parameters:
        xRange ((float, float)): The input interval over which the smooth transition occurs.
        yRange ((float, float)): The output range of the transition.
            The function smoothly interpolates between these values inside xRange.
        
    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Smoothstep)
    """
    return functions.spline(argument, [(xRange[0], yRange[0], 0), (xRange[1], yRange[1], 0)])

@macro
def tan(argument: AnyDensity, xRange: tuple[float, float] = (-1, 1)) -> Density[types.mul]:
    """Evaluates the tangent value of the input.

    Parameters:
        xRange ((float, float)): The interval over which the function can take inputs.
    """
    return sin(argument, xRange) / cos(argument, xRange)

@macro
def tanh(argument: AnyDensity, xRange: tuple[float, float] = (-1, 1)) -> Density[types.spline]:
    """Evaluates the hyperbolic tangent value of the input.

    Parameters:
        xRange ((float, float)): The interval over which the function can take inputs.
    """
    return functions.spline(argument, splines.sample_spline_points(py_math.tanh, xRange))

