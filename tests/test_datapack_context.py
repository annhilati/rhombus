from rhombus import Density, constant, Noise, noise
from rhombus.language import types
from beet import DataPack

def test_decoding_functions_with_context():

    with DataPack(path="test_pack") as dp:
        dp.clear()

        other = constant(1.0)

        d: Density = Density.partitioned(other) + 5.0

        d.inject(dp, "main:function")

        assert Density.from_datapack(dp, "main:function") == Density(types.add(types.Reference('rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', definition=types.constant(argument=1.0)), types.constant(argument=5.0)))

def test_decoding_DatapackResources_with_context():

    with DataPack(path="test_pack") as dp:
        dp.clear()

        n = Noise(-9, [1, 2, 3])

        # with exisiting Noise
        noise(n, 1, 1).inject(dp, "main:function")
        assert Density.from_datapack(dp, "main:function") == Density(types.noise(n, 1.0, 1.0))

        # with unknown Noise reference
        noise(Noise.referenced("some:noise"), 1, 1).inject(dp, "random:function")
        assert Density.from_datapack(dp, "random:function") == Density(types.noise(Noise.referenced("some:noise"), 1.0, 1.0))

test_decoding_DatapackResources_with_context()