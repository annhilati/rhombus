from rhombus.std import densityfunction, Density, macro, builtinmacro, vdft

def test_MacroWizard():

    @macro
    def fn(x: densityfunction) -> Density:
        return x
    
    assert fn(0) == Density(vdft.constant(0.0))
    assert fn("a:reference") == Density(vdft.Reference("a:reference"))