"""The `smath` module features Hermite spline approximations of common mathematical functions.
"""

import math as py_math
from math import sqrt, pi

from rhombus.std import Density, AnyDensity, functions, types, macro
from rhombus.macros import math
from rhombus import splines

__all__ = ["cos", "nPDF", "sin", "smoothstep"]


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
def erf(argument: AnyDensity, xRange: tuple[float, float] = (-3, 3)) -> Density[types.spline]:
    """Evaluates the value of the input on Gaussian error function."""
    return functions.spline(argument, splines.sample_spline_points(py_math.erf, xRange))

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
        center (float): The point about which the function is rotationally symmetric
        xRange ((float, float)): The interval over which the function can take inputs.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Logistic_function)
    """
    func = lambda x: capacity/(1+py_math.exp(- growth_rate * (x-center)))
    return functions.spline(argument, splines.sample_spline_points(func, xRange))

@macro
def nPDF(argument: AnyDensity, mean: float = 0, standard_deviation: float = 1/sqrt(2 * pi)) -> Density[types.spline]:
    """Evaluates the value of the input on a normal distributed probability density function.

    Parameters:
        mean (float): The center of the normal distribution.
        standard_deviation (float): Controlls the spread or dispersion of the function relative to its mean.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Normal_distribution)
    """
    pdf = lambda x: (
        1/(standard_deviation * py_math.sqrt(2 * py_math.pi))
        * py_math.exp(-0.5 * ((x - mean) / standard_deviation) ** 2)
    )
    return functions.spline(argument, splines.sample_spline_points(pdf, (mean - 3.5*standard_deviation, mean + 3.5*standard_deviation), 13))

@macro
def nCDF(argument: AnyDensity, mean: float = 0, standard_deviation: float = 1/sqrt(2 * pi)) -> Density[types.spline]:
    """Evaluates the value of the input on a normal distributed cumulative distribution function.

    Parameters:
        mean (float): The center of the normal distribution.
        standard_deviation (float): Controlls the spread or dispersion of the function relative to its mean.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Normal_distribution)
    """
    cdf = lambda x: 0.5 * (1 + py_math.erf((x - mean) / (standard_deviation * py_math.sqrt(2))))
    return functions.spline(argument, splines.sample_spline_points(cdf, (mean - 3.5*standard_deviation, mean + 3.5*standard_deviation), 13))

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
    input moves from `xRange[0]` to `xRange[1]`.<br> Outside the latter interval the output
    is clamped to the respective boundary value.

    Parameters:
        xRange ((float, float)): The input interval over which the smooth transition occurs.
        yRange ((float, float)): The output range of the transition.
            The function smoothly interpolates between these values inside xRange.
        
    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Smoothstep)
    """
    return functions.spline(argument, [(xRange[0], yRange[0], 0), (xRange[1], yRange[1], 0)])
