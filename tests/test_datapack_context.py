from rhombus import Density, constant, Noise, noise
from rhombus.std import vdft
from beet import DataPack
from beet.contrib import worldgen

def test_decoding_functions_from_datapack_by_identifier():

    with DataPack(path="test_pack") as dp:
        dp.clear()

        other = constant(1.0)

        d: Density = Density.partitioned(other) + 5.0

        d.inject(dp, "main:function")

        assert Density.from_datapack(dp, "main:function") == Density(vdft.add(
            vdft.Reference('rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', definition=vdft.constant(argument=1.0)),
            vdft.constant(argument=5.0))
        )

def test_decoding_DatapackResources_from_datapack_implicitely():

    with DataPack(path="test_pack") as dp:
        dp.clear()

        n = Noise(-9, [1, 2, 3])

        # with exisiting Noise
        noise(n, 1, 1).inject(dp, "main:function")
        assert Density.from_datapack(dp, "main:function") == Density(vdft.noise(n, 1.0, 1.0))

        # with unknown Noise reference
        noise(Noise.referenced("some:noise"), 1, 1).inject(dp, "random:function")
        assert Density.from_datapack(dp, "random:function") == Density(vdft.noise(Noise.referenced("some:noise"), 1.0, 1.0))
        
def test_decoding_DatapackResources_from_datapack_by_identifier():
    with DataPack(path="test_pack") as dp:
        dp.clear()

        n = Noise(-9, [1, 2, 3])
        
        dp["test:noise"] = worldgen.WorldgenNoise({"firstOctave": -9, "amplitudes": [1, 2, 3]})
        assert Noise.from_datapack(dp, "test:noise") == n