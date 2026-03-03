from Rhombus.language.density import MacroWizard, DensityDescriptor, Density
from Rhombus.language import dft

@MacroWizard
def linsqrt01(argument: DensityDescriptor) -> Density[dft.add]:
    return 0.41731 + 0.59016*argument

@MacroWizard
def ratsqrt01(argument: DensityDescriptor) -> Density[dft.mul]:
    return argument / (0.41731+0.59016*argument)
