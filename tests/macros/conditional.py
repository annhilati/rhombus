from rhombus import *
from rhombus.support.vanilla import types
from rhombus.support.vanilla.types import range_choice
from rhombus.core.density_function import Reference
from rhombus.core.utils import uuid_hash

when = conditional.when
EPS = env.infinitesimal


def test_logic():

    assert (when("in1").equals(0) & when("in2").equals(1)).then(10).otherwise(
        -10
    ) == Density(range_choice(
        "minecraft:in1",
        0.0,
        EPS,
        range_choice("minecraft:in2", 1.0, 1.0 + EPS, 10.0, -10.0),
        -10.0,
    ))

    assert (when("in1").equals(0) | when("in2").equals(1)).then(10).otherwise(
        -10
    ) == Density(range_choice(
        "minecraft:in1",
        0.0,
        EPS,
        10.0,
        range_choice("minecraft:in2", 1.0, 1.0 + EPS, 10.0, -10.0),
    ))


def test_alternatives():

    value = Density("minecraft:in").AST
    inp = Reference(
        "rhombus:partitioned/" + uuid_hash(value.serialize_toplevel()),
        definition=types.cache_once(value),
    )
    assert when("in").equals(-1).then(1).elsewhen("in").equals(1).then(-1).otherwise(
        0
    ) == Density(range_choice(
        inp,
        -1.0,
        -1.0 + EPS,
        types.constant(1.0),
        range_choice(inp, 1.0, 1.0 + EPS, types.constant(-1.0), types.constant(0.0)),
    ))
