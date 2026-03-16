from rhombus.language import DensityDescriptor, Density, types
from rhombus.language.density import MacroWizard, BuiltinWizard

def test_MacroWizard():

    @MacroWizard
    def macro(x: DensityDescriptor) -> Density:
        return x
    
    assert macro(0) == Density(types.constant(0.0))
    assert macro("a:reference") == Density(types.Reference("a:reference"))