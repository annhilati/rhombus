from rhombus.language.noise import Noise
from rhombus.language.density import Density, DensityDescriptor, BuiltinWizard
from rhombus.support.tectonic import types


@BuiltinWizard
def invert(argument: DensityDescriptor) -> Density[types.invert]:
    """Calculates `1/x`.
    """
    return Density(types.invert(argument))

def config_constant(key: str) -> Density[types.config_constant]:
    "References a constant from the Tectonic configuration."
    return Density(types.config_constant(key))

@BuiltinWizard
def config_noise(noise: Noise, key: str, shift_x: DensityDescriptor, shift_z: DensityDescriptor) -> Density[types.config_noise]:
    ""
    return Density(types.config_noise(noise, key, shift_x, shift_z))