import pytest
from rhombus.core.environment import parse_version_specifier

def test_parse_datapack_version():
    assert parse_version_specifier(41.0) == (41, 0)
    assert parse_version_specifier(41) == (41, 0)

def test_parse_version_tuple():
    assert parse_version_specifier((1, 20)) == (1, 20)
    assert parse_version_specifier("1.19.2") == (1, 19, 2)


def test_require_module_version():
    from rhombus import rho, vanilla
    rho.require({vanilla: "1.20.1"})
    assert rho.versions["datapack"] == (15, 0)
    assert rho.datapack_version == 15.0


def test_require_extension_default():
    from rhombus import rho, vanilla
    rho.require({vanilla: ...})
    assert rho.versions["datapack"] == (125, 1)
