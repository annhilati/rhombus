from rhombus.std import Noise

def test_deserialize():
    
    # File Data
    assert Noise.deserialize_toplevel({"firstOctave": -8, "amplitudes": [0, 1, 2]}) == Noise(-8, [0, 1, 2])
    
    # Reference
    n = Noise(None, None)
    n.identifier = "some:noise"
    assert Noise.deserialize_inline("some:noise") == n
    