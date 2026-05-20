from rhombus.std import Density, AnyDensity, vdft

def test_unify_values():
    
    # int
    assert AnyDensity.unify(1) == Density(vdft.constant(1.0))
    
    # float
    assert AnyDensity.unify(4.5) == Density(vdft.constant(4.5))
    
    # str
    assert AnyDensity.unify("test:reference") == Density(vdft.Reference("test:reference"))
    
    # DensityFunction
    assert AnyDensity.unify(vdft.constant(1.0)) == Density(vdft.constant(1.0))