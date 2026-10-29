from rhombus.std.noise import Noise
from rhombus.std.builtin.density import Density, AnyDensity
from rhombus.std.builtin.macros import macro

from . import types


@macro
def invert(df: AnyDensity) -> Density:
    """Calculates the reciprocal value of the input."""
    return Density(types.invert(df.build()))


@macro
def clamp(df: AnyDensity, min: AnyDensity, max: AnyDensity) -> Density:
    """Clamps the input between two density functions."""
    return Density(types.config_clamp(df.build(), min.build(), max.build()))
    

@macro
def config_constant(key: str) -> Density:
    "References a constant from the Tectonic configuration."
    return Density(types.config_constant(key))


@macro
def config_noise(
    noise: Noise, key: str, shift_x: AnyDensity, shift_z: AnyDensity
) -> Density:
    ""
    return Density(types.config_noise(noise, key, shift_x.build(), shift_z.build()))
