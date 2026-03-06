from Rhombus.language.density import Density, DensityDescriptor, MacroWizard
from Rhombus.language import dft, functions as f
from Rhombus.macros import math as m, _spline as s

__all__ = []

@MacroWizard
def smoothstep(argument: DensityDescriptor, xRange: tuple[float, float] = (-1, 1), yRange: tuple[float, float] = (-1, 1)) -> Density[dft.spline]:
    # xRange and yRange are not selection but transformation intervals
    return f.spline(argument, [(xRange[0], yRange[0], 0), (xRange[1], yRange[1], 0)])

