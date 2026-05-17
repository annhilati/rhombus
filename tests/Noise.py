from rhombus.std import Noise

def test_deserialize():
    
    assert Noise.deserialize_toplevel({"firstOctave": -8, "amplitudes": [0, 1, 2]}) == Noise(-8, [0, 1, 2])