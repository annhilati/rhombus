from rhombus import Density
from rhombus.support.vanilla import types
from rhombus.runtime import rho

import beet
import beet.contrib.worldgen as worldgen


def test_partitioning():

    assert Density.partitioned(1.0).AST.build() == (
        types.Reference(
            "rhombus:generated/d0ff5974b6aa52cf562bea5921840c03",
            definition=types.constant(value=1.0),
        )
    )

    assert ("test" @ Density(1.0)).AST.build() == (
        types.Reference("minecraft:test", definition=types.constant(value=1.0))
    )

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
    assert Density(1).AST == Density(types.constant(1.0)).AST

    # float
    assert Density(4.5).AST == Density(types.constant(4.5)).AST

    # str
    assert Density("test:reference").AST == Density(types.Reference("test:reference")).AST

    # DensityFunction
    assert Density(types.constant(1.0)).AST == Density(types.constant(1.0)).AST
