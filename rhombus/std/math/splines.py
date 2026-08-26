__all__ = [
    "atan",
    "cos",
    "coth",
    "normalCDF",
    "normalPDF",
    "sin",
    "smoothstep",
    "tan",
    "tanh",
    "erf",
    "logistic",
]

import math as py_math
from math import sqrt, pi, e

from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro
from rhombus.std.math import _splinelib
from rhombus.std import math
from rhombus.support import vanilla as vt


@macro
def erf(
    argument: AnyDensity, domain: tuple[float, float] = (-3, 3)
) -> Density[vt.spline]:
    """Evaluates the value of the input on Gaussian error function."""
    points = max(5, round((domain[1] - domain[0]) / 1.5) + 1)
    return math.spline(
        argument, _splinelib.sample_spline_points(py_math.erf, domain, points)
    )


@macro
def exp(
    argument: AnyDensity, domain: tuple[float, float] = (-1, 1), base: float = e
) -> Density[vt.spline]:
    """Evaluates the value of the input on an exponential function."""
    func = lambda x: base**x
    points = max(5, round((domain[1] - domain[0]) / 1.5) + 1)
    return math.spline(
        argument, _splinelib.sample_spline_points(func, domain, points)
    )


@macro
def logistic(
    argument: AnyDensity,
    capacity: float = 1,
    growth_rate: float = 4,
    center: float = 0,
    domain: tuple[float, float] = (-1, 1),
) -> Density[vt.spline]:
    """Evaluates the value of the input on a logistic function.

    Parameters:
        capacity (float):
        growth_rate (float): Controlls the steepness of the curve.
        center (float): The point around which the function is rotationally symmetric.
        domain ((float, float)): The interval over which the function can take inputs.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Logistic_function)
    """
    func = lambda x: capacity / (1 + py_math.exp(-growth_rate * (x - center)))
    points = max(5, round((domain[1] - domain[0]) / 1.5) + 1)
    return math.spline(
        argument, _splinelib.sample_spline_points(func, domain, points)
    )


@macro
def normalPDF(
    argument: AnyDensity, mean: float = 0, standard_deviation: float = 1 / sqrt(2 * pi)
) -> Density[vt.spline]:
    """Evaluates the value of the input on a normal distributed probability density function.

    Parameters:
        mean (float): The center of the normal distribution.
        standard_deviation (float): Controlls the spread or dispersion of the function relative to its mean.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Normal_distribution)
    """
    func = lambda x: (
        1
        / (standard_deviation * py_math.sqrt(2 * py_math.pi))
        * py_math.exp(-0.5 * ((x - mean) / standard_deviation) ** 2)
    )
    return math.spline(
        argument,
        _splinelib.sample_spline_points(
            func, (mean - 3.5 * standard_deviation, mean + 3.5 * standard_deviation), 13
        ),
    )


@macro
def normalCDF(
    argument: AnyDensity, mean: float = 0, standard_deviation: float = 1 / sqrt(2 * pi)
) -> Density[vt.spline]:
    """Evaluates the value of the input on a normal distributed cumulative distribution function.

    Parameters:
        mean (float): The center of the normal distribution.
        standard_deviation (float): Controlls the spread or dispersion of the function relative to its mean.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Normal_distribution)
    """
    func = lambda x: (
        0.5 * (1 + py_math.erf((x - mean) / (standard_deviation * py_math.sqrt(2))))
    )
    return math.spline(
        argument,
        _splinelib.sample_spline_points(
            func, (mean - 3.5 * standard_deviation, mean + 3.5 * standard_deviation), 13
        ),
    )


@macro
def smoothstep(
    argument: AnyDensity,
    domain: tuple[float, float] = (-1, 1),
    range: tuple[float, float] = (-1, 1),
) -> Density[vt.spline]:
    """Evaluates a smoothstep transition of the input.

    The smoothstep curve rises smoothly from `yRange[0]` to `yRange[1]` while the
    input moves from `domain[0]` to `domain[1]`. Outside the latter interval the output
    is clamped to the respective boundary value.

    Parameters:
        domain ((float, float)): The input interval over which the smooth transition occurs.
        range ((float, float)): The output range of the transition.
            The function smoothly interpolates between these values inside domain.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Smoothstep)
    """
    return math.spline(
        argument, [(domain[0], range[0], 0), (domain[1], range[1], 0)]
    )


