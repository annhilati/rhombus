from Rhombus.language import DensityDescriptor, Density, dft
from Rhombus.language.density import MacroWizard, BuiltinWizard

def test_MacroWizard():

    @MacroWizard
    def macro(x: DensityDescriptor) -> Density:
        return x
    
    assert macro(0) == Density(dft.constant(0.0))
    assert macro("a:reference") == Density(dft.Reference("a:reference"))