from Rhombus import Density, constant, Noise, noise
from Rhombus.support.builtin import dft
from beet import DataPack

def test_decoding_functions_with_context():

    with DataPack(path="test_pack") as dp:
        dp.clear()

        other = constant(1.0)

        d: Density = Density.separated(other) + 5.0

        d.inject(dp, "main:function", log=False)

        assert Density.from_datapack(dp, "main:function") == Density(dft.add(dft.Reference('rhombus:generated/d0ff5974b6aa52cf562bea5921840c03', default=dft.constant(argument=1.0)), dft.constant(argument=5.0)))

def test_decoding_RegistryResources_with_context():

    with DataPack(path="test_pack") as dp:
        dp.clear()

        n = Noise(-9, [1, 2, 3])

        # with exisiting Noise
        noise(n, 1, 1).inject(dp, "main:function", log=False)
        assert Density.from_datapack(dp, "main:function") == Density(dft.noise(n, 1.0, 1.0))

        # with unknown Noise reference
        noise(Noise.referenced("some:noise"), 1, 1).inject(dp, "random:function", log=False)
        assert Density.from_datapack(dp, "random:function") == Density(dft.noise(Noise(None, None, "some:noise"), 1.0, 1.0))