from rhombus.std.noise import Noise
from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro

from . import types


@macro
def invert(argument: AnyDensity) -> Density:
    """Calculates `1/x`."""
    return Density(types.invert(argument.AST))


def config_constant(key: str) -> Density:
    "References a constant from the Tectonic configuration."
    return Density(types.config_constant(key))


@macro
def config_noise(
    noise: Noise, key: str, shift_x: AnyDensity, shift_z: AnyDensity
) -> Density:
    ""
    return Density(types.config_noise(noise, key, shift_x.AST, shift_z.AST))
