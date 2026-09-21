from rhombus.runtime import rho
from rhombus import Density
from rhombus.support.vanilla import types
from rhombus.core import environment
import beet
import beet.contrib.worldgen as worldgen


def test_partitioning():

    assert Density.partitioned(1.0).is_identical(Density(
        types.Reference(
            "rhombus:partitioned/d0ff5974b6aa52cf562bea5921840c03",
            definition=types.constant(value=1.0),
        )
    ))

    assert ("test" @ Density(1.0)).is_identical(Density(
        types.Reference("minecraft:test", definition=types.constant(value=1.0))
    ))

    with beet.DataPack(path="test_pack_hfcbsjfi4") as dp:
        old_dp = rho.datapack
        rho.datapack = dp

        dp.clear()

        ("a:config" @ Density(3.14)).implement(dp, "main:function")
        assert dp[worldgen.WorldgenDensityFunction][
            "a:config"
        ] == worldgen.WorldgenDensityFunction(3.14)

        rho.datapack = old_dp


def test_unify_values():

    # int
    assert Density(1).is_identical(Density(types.constant(1.0)))

    # float
    assert Density(4.5).is_identical(Density(types.constant(4.5)))

    # str
    assert Density("test:reference").is_identical(Density(types.Reference("test:reference")))

    # DensityFunction
    assert Density(types.constant(1.0)).is_identical(Density(types.constant(1.0)))
