from rhombus import Density, Noise
from rhombus.language import types
from rhombus.support.moredfs import RandomSampler, types as mdft

def test_Density_from_dict():
    
    # literal constants
    assert Density.from_dict({"type": "abs", "argument": 1.0}) == Density(types.abs(types.constant(1.0)))
    
    # nested functions
    assert Density.from_dict({"type": "abs", "argument": {"type": "abs", "argument": 1.0}}) == Density(types.abs(types.abs(types.constant(1.0))))

    # literal references
    assert Density.from_dict({"type": "abs", "argument": "test:reference"}) == Density(types.abs(types.Reference("test:reference")))

    # DatapackResources
    assert Density.from_dict({"type": "noise", "noise": "referenced:noise", "xz_scale": 1, "y_scale": 1}) == Density(types.noise(noise=Noise.referenced('referenced:noise'), xz_scale=1, y_scale=1))

    # SubParameters
    assert Density.from_dict({
        "type": "moredfs:value_noise",
        "sampler": {
            "type": "beta",
            "alpha": 0,
            "beta": 0
        },
        "size_x": 0,
        "size_y": 0,
        "size_z": 0,
        "interpolation": "none"
        }) == Density(mdft.value_noise(RandomSampler.Beta(0, 0), 0, 0, 0, "none"))