import beet
import beet.contrib.worldgen as worldgen

from rhombus.core import DensityFunction, constant, Reference
# only core Modules

def test_deserialize_dicts_with_type_key():
    
    assert DensityFunction.deserialize({"type": "minecraft:constant", "argument": 3.14}) == constant(3.14)
    

def test_deserialize_literals():
    
    # Constants
    assert DensityFunction.deserialize(3.14) == constant(3.14)
    
    # References
    assert DensityFunction.deserialize("some:reference") == Reference("some:reference")
    
    # References with available context
    with beet.DataPack(path="test_pack") as dp:
        dp.clear()
        
        dp["some:function"] = worldgen.WorldgenDensityFunction({"type": "minecraft:constant", "argument": 3.14})
        
        assert DensityFunction.deserialize("some:function", dp=dp) == Reference("some:function", definition=constant(3.14))
        
        
def test_serialize_literals():
    
    # Constants
    assert constant(3.14).serialize() == 3.14
    
    # References
    assert Reference("some:reference").serialize()                            == "some:reference"
    assert Reference("some:reference", definition=constant(3.14)).serialize() == "some:reference"
    
    from rhombus.std import vdft
    assert Reference("some:reference").serialize(inline=False) == {"type": "minecraft:add", "argument1": "some:reference", "argument2": 0.0} # Be aware of the order of arguments