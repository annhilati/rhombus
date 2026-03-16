from rhombus import noise, Noise

n = Noise(-9, [1, 2, 3])

def test_identifier_generation():

    # DatapackResources
    assert noise(n, 1, 1).as_dict() == {'type': 'minecraft:noise', 'noise': 'rhombus:generated/d6bc8d10b66669f23fdc8cc0606fcd83', 'xz_scale': 1, 'y_scale': 1}