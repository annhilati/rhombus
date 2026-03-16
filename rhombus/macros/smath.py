from rhombus.language.density import Density, DensityDescriptor, MacroWizard
from rhombus.language import functions as f, types
from rhombus.macros import math as m, _spline as s
from math import pi, sqrt
import math as _math

__all__ = ["cos", "PDF", "sin", "smoothstep"]


@MacroWizard
def cos(argument: DensityDescriptor, xRange: tuple[float, float] = (-pi, pi)) -> Density[types.spline]:
    """Evaluates the cosine value of the input.

    Parameters:
        xRange ((float, float)): The interval over which the function can take inputs.
    """
    points = max(round(2 * (xRange[1] - xRange[0]) / pi + 1), 3)
    return f.spline(argument, s.function_spline_points(_math.cos, xRange, points))

@MacroWizard
def logistic(argument: DensityDescriptor, capacity: float = 1, growth_rate: float = 4, center: float = 0, xRange: tuple[float, float] = (-1, 1)) -> Density[types.spline]:
    """Evaluates the value of the input on a logistic function.

    Parameters:
        capacity (float): 
        growth_rate (float): Controlls the steepness of the curve.
        center (float): The point about which the function is rotationally symmetric
        xRange ((float, float)): The interval over which the function can take inputs.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Logistic_function)
    """
    func = lambda x: capacity/(1+_math.exp(- growth_rate * (x-center)))
    return f.spline(argument, s.function_spline_points(func, xRange))

@MacroWizard
def PDF(argument: DensityDescriptor, mean: float = 0, standard_deviation: float = 1/sqrt(2 * pi)) -> Density[types.spline]:
    """Evaluates the value of the input on a probability density function.

    Parameters:
        mean (float): The center of the normal distribution.
        standard_deviation (float): Controlls the spread or dispersion of the function relative to its mean.

    ---
    [Wikipedia](https://en.wikipedia.org/wiki/Normal_distribution)
    """
    pdf = lambda x: 1/(standard_deviation * _math.sqrt(2 * _math.pi)) * _math.exp(-0.5 * ((x - mean) / standard_deviation) ** 2)
    return f.spline(argument, s.function_spline_points(pdf, (mean - 3.5*standard_deviation, mean + 3.5*standard_deviation), 13))

@MacroWizard
def sin(argument: DensityDescriptor, xRange: tuple[float, float] = (-pi, pi)) -> Density[types.spline]:
    """Evaluates the sine value of the input.

    Parameters:
        xRange ((float, float)): The interval over which the function can take inputs.
    """
    points = max(round(2 * (xRange[1] - xRange[0]) / pi + 1), 3)
    return f.spline(argument, s.function_spline_points(_math.sin, xRange, points))

@MacroWizard
def smoothstep(argument: DensityDescriptor, xRange: tuple[float, float] = (-1, 1), yRange: tuple[float, float] = (-1, 1)) -> Density[types.spline]:
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
    return f.spline(argument, [(xRange[0], yRange[0], 0), (xRange[1], yRange[1], 0)])
