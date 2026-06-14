import beet
import beet.contrib.worldgen as worldgen

from rhombus.core import DensityFunction, constant, Reference
# only core Modules
from rhombus import config

def test_deserialize_dicts_with_type_key():
    
    assert DensityFunction.deserialize_toplevel({"type": "minecraft:constant", "argument": 3.14}) == constant(3.14)
    

def test_deserialize_literals():
    
    # Constants
    assert DensityFunction.deserialize_inline(3.14) == constant(3.14)
    
    # References
    assert DensityFunction.deserialize_inline("some:reference") == Reference("some:reference")
    
    # References with available context
    with beet.DataPack(path="test_pack_hfcbsjfi4") as dp:
        
        token = config.ctx.datapack.set(dp)
        
        dp.clear()
        
        dp["some:function"] = worldgen.WorldgenDensityFunction({"type": "minecraft:constant", "argument": 3.14})
        
        assert DensityFunction.deserialize_inline("some:function") == Reference("some:function", constant(3.14))
       
        config.ctx.datapack.reset(token)
        
        
def test_serialize_literals():
    
    # Constants
    assert constant(3.14).serialize_inline() == 3.14
    
    # References
    assert Reference("some:reference").serialize_inline()                            == "some:reference"
    assert Reference("some:reference", definition=constant(3.14)).serialize_inline() == "some:reference"
    
    assert Reference("some:reference").serialize_toplevel() == {"type": "minecraft:add", "argument1": "some:reference", "argument2": 0.0}
        # Be aware of the order of arguments