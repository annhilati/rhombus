import pytest
from rhombus.core.environment import parse_version_specifier_NEW

def test_parse_datapack_version():
    assert parse_version_specifier_NEW(41.0) == (41, 0)
    assert parse_version_specifier_NEW(41) == (41, 0)

def test_parse_version_tuple():
    assert parse_version_specifier_NEW((1, 20)) == (1, 20)
    assert parse_version_specifier_NEW("1.19.2") == (1, 19, 2)
