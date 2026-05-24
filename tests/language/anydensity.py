from rhombus.std import Density, AnyDensity, types

def test_unify_values():
    
    # int
    assert AnyDensity.unify(1) == Density(types.constant(1.0))
    
    # float
    assert AnyDensity.unify(4.5) == Density(types.constant(4.5))
    
    # str
    assert AnyDensity.unify("test:reference") == Density(types.Reference("test:reference"))
    
    # DensityFunction
    assert AnyDensity.unify(types.constant(1.0)) == Density(types.constant(1.0))