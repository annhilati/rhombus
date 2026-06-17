from rhombus.std import Noise

def test_deserialization():
    
    # File Data
    assert Noise.from_dict({"firstOctave": -8, "amplitudes": [0.0, 1.0, 2.0]}) == Noise(-8, [0.0, 1.0, 2.0])
    
    # Reference
    n = Noise(None, None)
    setattr(n, "identifier", "some:noise")
    assert Noise.deserialize_inline("some:noise") == n