from rhombus.language import Noise, Density, densityfunction, builtinmacro
from rhombus.support.tectonic import types


@builtinmacro
def invert(argument: densityfunction) -> Density[types.invert]:
    """Calculates `1/x`.
    """
    return Density(types.invert(argument))

def config_constant(key: str) -> Density[types.config_constant]:
    "References a constant from the Tectonic configuration."
    return Density(types.config_constant(key))

@builtinmacro
def config_noise(noise: Noise, key: str, shift_x: densityfunction, shift_z: densityfunction) -> Density[types.config_noise]:
    ""
    return Density(types.config_noise(noise, key, shift_x, shift_z))