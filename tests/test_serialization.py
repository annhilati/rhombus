from rhombus.std import Noise, vdft
from rhombus.core.serializer import serialize_any, deserialize_any

def test_DataPackResource():
    r = Noise(5, [1])
    
    assert r.as_dict() == {'firstOctave': 5, 'amplitudes': [1]}
    
    
def test_DensityFunction():
    
    ast = vdft.add(vdft.constant(1.0), vdft.Reference("some:df"))
    assert ast.serialize() == {'type': 'minecraft:add', 'argument1': 1.0, 'argument2': 'some:df'}
    
    
if __name__ == "__main__":
    test_DensityFunction()
    
    print(deserialize_any("some:noise", Noise))