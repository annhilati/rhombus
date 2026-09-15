import pytest
from rhombus.core.environment import parseVersionString, _parse_version_specifier

def test_parse_version_string():
    assert parseVersionString("1.20") == (1, 20)
    assert parseVersionString("1.20.4") == (1, 20, 4)

def test_parse_version_specifier_float():
    assert _parse_version_specifier(41.0) == ("datapack", (41, 0))
    assert _parse_version_specifier(41) == ("datapack", (41, 0))

def test_parse_version_specifier_tuple():
    assert _parse_version_specifier(("my_mod", (1, 20))) == ("my_mod", (1, 20))
    assert _parse_version_specifier(("my_mod", "1.19.2")) == ("my_mod", (1, 19, 2))
