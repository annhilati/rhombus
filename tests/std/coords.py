import pytest
from rhombus import rho
from rhombus.std.coords import gradient


def test_gradient_legacy_extrapolate():
    rho.set_version(minecraft="1.20")
    g = gradient("y", 0, 100, 0, 1, tiling="extrapolate")
    built = g.build()

    assert built.from_y == -4064
    assert built.to_y == 4062
    assert round(built.from_value, 2) == -40.64
    assert round(built.to_value, 2) == 40.62


def test_gradient_legacy_clamped():
    rho.set_version(minecraft="1.20")
    g = gradient("y", 10, 50, 0, 1, tiling="clamp_to_edge")
    built = g.build()

    assert built.from_y == 10
    assert built.to_y == 50
    assert built.from_value == 0.0
    assert built.to_value == 1.0


def test_gradient_legacy_axis_restriction():
    rho.set_version(minecraft="1.20")
    g = gradient("x", 0, 100, 0, 1)
    with pytest.raises(NotImplementedError):
        g.build()


def test_gradient_equal_coordinates():
    with pytest.raises(ValueError):
        gradient("y", 50, 50, 0, 1).build()


def test_gradient_modern():
    rho.set_version(datapack=113)
    g = gradient("x", 0, 100, 0, 1, tiling="extrapolate")
    built = g.build()
    assert built.axis == "x"
    assert built.tiling == "clamp_to_edge"
