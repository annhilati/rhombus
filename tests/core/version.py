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

def test_rhombus_version_tuple_string_parts():
    v = RhombusVersion(("my_mod", (1, 20, "rc4")))
    assert v.namespace == "my_mod"
    assert v.version == (1, 20, "rc4")

def test_rhombus_version_tuple_of_ints():
    v = RhombusVersion(("my_mod", (1, 20)))
    assert v.namespace == "my_mod"
    assert v.version == (1, 20)

def test_rhombus_version_string_fails():
    with pytest.raises(TypeError):
        RhombusVersion("1.19.2")

def test_rhombus_version_equality():
    assert RhombusVersion(41.0) == RhombusVersion(41)
    assert RhombusVersion(41.0) == RhombusVersion(("datapack", (41,)))
    assert RhombusVersion(("mod", (1, 0))) == RhombusVersion(("mod", (1,)))

def test_rhombus_version_comparison():
    assert RhombusVersion(41.0) < RhombusVersion(42.0)
    assert RhombusVersion(("mod", (1,))) < RhombusVersion(("mod", (1, 1)))
    assert RhombusVersion(("mod", (1, 19, 2))) >= RhombusVersion(("mod", (1, 19)))
    assert RhombusVersion(111.0) >= RhombusVersion(111)

def test_rhombus_version_natural_sorting():
    assert RhombusVersion(("mod", (1, 20, "rc1"))) < RhombusVersion(("mod", (1, 20, "rc10")))
    assert RhombusVersion(("mod", (1, 20, "rc2"))) > RhombusVersion(("mod", (1, 20, "rc1")))
    
def test_rhombus_version_string_vs_int():
    # Pre-release (string) should be considered less than final (int) if the int is 0 (omitted padding).
    # e.g., 1.20.rc1 is smaller than 1.20.0
    assert RhombusVersion(("mod", (1, 20, "rc1"))) < RhombusVersion(("mod", (1, 20)))
    assert RhombusVersion(("mod", (1, 20, "rc1"))) < RhombusVersion(("mod", (1, 20, 0)))
