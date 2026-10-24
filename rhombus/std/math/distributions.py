__all__ = [
    "erf",
    "logistic",
    "normalCDF",
    "normalPDF",
]

import math as py_math
from math import sqrt, pi

from rhombus.std.builtin.density import Density, AnyDensity
from rhombus.std.builtin.macros import macro
from rhombus.std.math import _splinelib
from rhombus.std import math


@macro
def erf(argument: AnyDensity) -> Density:
    """Calculates the value of the input on the Gaussian error function."""
    return math.spline(
        argument, _splinelib.sample_spline_points(py_math.erf, (-2.5, 2.5), 5)
    )


@macro
def logistic(
    argument: AnyDensity,
    capacity: float = 1,
    growth_rate: float = 4,
    center: float = 0,
) -> Density:
    """Calculates the value of the input on a logistic function.

    Parameters:
        capacity (float): The upper bound the function approaches.
        growth_rate (float): Controlls the steepness of the curve.
        center (float): The point around which the function is rotationally symmetric.
        domain ((float, float)): The interval over which the function can take inputs.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Logistic_function)
    """
    func = lambda x: capacity / (1 + py_math.exp(-growth_rate * (x - center)))
    product = capacity * growth_rate

    if capacity <= 0 or growth_rate <= 0 or product <= 0.04:
        # No interval with slope strictly greater than 0.01.
        # Use a safe, symmetric fallback domain.
        domain = (center - 10 / growth_rate,
                  center + 10 / growth_rate)
    else:
        root = sqrt(product * (product - 0.04))

        z_plus = (product - 0.02 + root) / 0.02
        z_minus = (product - 0.02 - root) / 0.02

        x_left = center - py_math.log(z_plus) / growth_rate
        x_right = center - py_math.log(z_minus) / growth_rate

        domain = (x_left, x_right)

    return math.spline(
        argument,
        _splinelib.sample_spline_points(func, domain, 7)
    )


@macro
def normalPDF(
    argument: AnyDensity, mean: float = 0, standard_deviation: float = 1 / sqrt(2 * pi)
) -> Density:
    """Calculates the value of the input on a normal distributed probability density function.

    Parameters:
        mean (float): The center of the normal distribution.
        standard_deviation (float): Controlls the spread or dispersion of the function relative to its mean.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Normal_distribution)
    """
    func = lambda x: (
        1 / (standard_deviation * py_math.sqrt(2 * py_math.pi))
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
) -> Density:
    """Calculates the value of the input on a normal distributed cumulative distribution function.

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
