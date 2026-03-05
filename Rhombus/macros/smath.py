from Rhombus.language.density import MacroWizard, Density, DensityDescriptor
from Rhombus.language import dft, functions as f
from Rhombus.macros import _spline as s

@MacroWizard
def smoothstep(argument: DensityDescriptor) -> Density[dft.spline]:
    return f.spline(argument, s.poly_spline_points(-2, 3, 0, 0, (0, 1)))