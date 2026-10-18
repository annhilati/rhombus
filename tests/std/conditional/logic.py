from rhombus import *
from rhombus.support.vanilla import types
from rhombus.support.vanilla.types import range_choice
from rhombus.std.conditional import when

EPS = 1e-7


def test_logic():

    assert (when("in1").equals(0) & when("in2").equals(1)).then(10).otherwise(
        -10
    ).build() == range_choice(
        "minecraft:in1",
        0.0,
        EPS,
        range_choice("minecraft:in2", 1.0, 1.0 + EPS, 10.0, -10.0),
        -10.0,
    )

    assert (when("in1").equals(0) | when("in2").equals(1)).then(10).otherwise(
        -10
    ).build() == range_choice(
        "minecraft:in1",
        0.0,
        EPS,
        10.0,
        range_choice("minecraft:in2", 1.0, 1.0 + EPS, 10.0, -10.0),
    )


def test_alternatives():
    assert when("in").equals(-1).then(1).elsewhen("in").equals(1).then(-1).otherwise(
        0
    ).build() == range_choice(
        "minecraft:in",
        -1.0,
        -1.0 + EPS,
        types.constant(1.0),
        range_choice("minecraft:in", 1.0, 1.0 + EPS, types.constant(-1.0), types.constant(0.0)),
    )
