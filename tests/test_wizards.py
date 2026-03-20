from rhombus.language import DensityDescriptor, Density, types, macro, builtinmacro

def test_MacroWizard():

    @macro
    def fn(x: DensityDescriptor) -> Density:
        return x
    
    assert fn(0) == Density(types.constant(0.0))
    assert fn("a:reference") == Density(types.Reference("a:reference"))