from rhombus import Density
from rhombus.std import vdft

def test_partitioning_factories():

    assert Density.partitioned(1.0) == Density(vdft.Reference(reference='rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', definition=vdft.constant(argument=1.0)))
    
    assert Density.configured("test", 1.0) == Density(vdft.Reference(reference='minecraft:test', definition=vdft.constant(argument=1.0)))