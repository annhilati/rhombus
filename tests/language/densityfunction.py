from rhombus.std import Density, densityfunction, vdft

def test_unify_values():
    
    # int
    assert densityfunction.unify(1) == Density(vdft.constant(1.0))
    
    # float
    assert densityfunction.unify(4.5) == Density(vdft.constant(4.5))
    
    # str
    assert densityfunction.unify("test:reference") == Density(vdft.Reference("test:reference"))
    
    # DensityFunction
    assert densityfunction.unify(vdft.constant(1.0)) == Density(vdft.constant(1.0))