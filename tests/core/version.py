import pytest
from rhombus.core.environment import RhombusVersion

def test_rhombus_version_float():
    v = RhombusVersion(41.0)
    assert v.namespace == "datapack"
    assert v.version == (41, 0)

def test_rhombus_version_int():
    v = RhombusVersion(41)
    assert v.namespace == "datapack"
    assert v.version == (41, 0)

def test_rhombus_version_tuple():
    v = RhombusVersion(("my_mod", "1.20.4-beta"))
    assert v.namespace == "my_mod"
    assert v.version == (1, 20, 4)

def test_rhombus_version_tuple_of_ints():
    v = RhombusVersion(("my_mod", (1, 20)))
    assert v.namespace == "my_mod"
    assert v.version == (1, 20)

def test_rhombus_version_string():
    v = RhombusVersion("1.19.2")
    assert v.namespace == "datapack"
    assert v.version == (1, 19, 2)

def test_rhombus_version_equality():
    assert RhombusVersion(41.0) == RhombusVersion(41)
    assert RhombusVersion(41.0) == RhombusVersion(("datapack", (41,)))
    assert RhombusVersion(("mod", (1, 0))) == RhombusVersion(("mod", (1,)))

def test_rhombus_version_comparison():
    assert RhombusVersion(41.0) < RhombusVersion(42.0)
    assert RhombusVersion(("mod", (1,))) < RhombusVersion(("mod", (1, 1)))
    assert RhombusVersion(("mod", (1, 19, 2))) >= RhombusVersion(("mod", (1, 19)))
    assert RhombusVersion(111.0) >= RhombusVersion(111)
