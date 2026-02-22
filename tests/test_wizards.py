from Rhombus.language import MacroWizard, BuiltinWizard, DensityDescriptor, Density, dft

def test_MacroWizard():

    @MacroWizard
    def macro(x: DensityDescriptor) -> Density:
        return x
    
    assert macro(0) == Density(dft.constant(0.0))
    assert macro("a:reference") == Density(dft.Reference("a:reference"))