from rhombus import Density
from rhombus.std import types
from rhombus import config
import beet
import beet.contrib.worldgen as worldgen

def test_partitioning():

    assert Density.partitioned(1.0) == Density(types.Reference(reference='rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', definition=types.constant(argument=1.0)))
    
    assert Density.configured("test", 1.0) == Density(types.Reference(reference='minecraft:test', definition=types.constant(argument=1.0)))
    
    with beet.DataPack(path="test_pack_hfcbsjfi4") as dp:
        
        token = config.ctx.datapack.set(dp)
        
        dp.clear()
        
        Density.configured("a:config", 3.14).inject(dp, "main:function")
        
        assert dp[worldgen.WorldgenDensityFunction]["a:config"] == worldgen.WorldgenDensityFunction(3.14)
       
        config.ctx.datapack.reset(token)