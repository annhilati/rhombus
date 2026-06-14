from rhombus import *
when = conditional.when

def test_logic():
    
    assert (when("in1").equals(0) & when("in2").equals(1)).then(10).otherwise(-10) ==\
        range_choice("minecraft:in1", 0.0, 2e-08, range_choice("minecraft:in2", 1.0, 1.0000000199999999, 10.0, -10.0), -10.0)

    assert (when("in1").equals(0) | when("in2").equals(1)).then(10).otherwise(-10) ==\
        range_choice("minecraft:in1", 0.0, 2e-08, 10.0, range_choice("minecraft:in2", 1.0, 1.0000000199999999, 10.0, -10.0))

def test_alternatives():
    
    assert when("in").equals(-1).then(1).elsewhen("in").equals(1).then(-1).otherwise(0) ==\
        range_choice("minecraft:in", -1.0, -0.9999999799999999, 1.0, range_choice("minecraft:in", 1.0, 1.0000000199999999, -1.0, 0.0))