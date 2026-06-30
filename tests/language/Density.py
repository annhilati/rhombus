from rhombus import Density
from rhombus.std import types
from rhombus.core import config
import beet
import beet.contrib.worldgen as worldgen

def test_partitioning():

    assert Density.partitioned(1.0) == Density(types.Reference('rhombus:partitioned/d0ff5974b6aa52cf562bea5921840c03', definition=types.constant(argument=1.0)))
    
    assert Density.configured("test", 1.0) == Density(types.Reference('minecraft:test', definition=types.constant(argument=1.0)))
    
    with beet.DataPack(path="test_pack_hfcbsjfi4") as dp:
        
        old_dp = config.ctx.datapack
        config.ctx.datapack = dp
        
        dp.clear()
        
        Density.configured("a:config", 3.14).inject(dp, "main:function")
        assert dp[worldgen.WorldgenDensityFunction]["a:config"] == worldgen.WorldgenDensityFunction(3.14)
       
        config.ctx.datapack = old_dp
        

def test_unify_values():
    
    # int
    assert Density.constant(1) == Density(types.constant(1.0))
    
    # float
    assert Density.constant(4.5) == Density(types.constant(4.5))
    
    # str
    assert Density.constant("test:reference") == Density(types.Reference("test:reference"))
    
    # DensityFunction
    assert Density.constant(types.constant(1.0)) == Density(types.constant(1.0))
    
def test_other():
    from rhombus import coords
    
    # __len__
    assert len(coords.x()) == 312