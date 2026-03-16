from rhombus.language.noise import Noise
from rhombus.language.density import Density, DensityDescriptor, BuiltinWizard
from rhombus.support.tectonic import dft


@BuiltinWizard
def invert(argument: DensityDescriptor) -> Density[dft.invert]:
    """Calculates `1/x`.
    """
    return Density(dft.invert(argument))

def config_constant(key: str) -> Density[dft.config_constant]:
    "References a constant from the Tectonic configuration."
    return Density(dft.config_constant(key))

@BuiltinWizard
def config_noise(noise: Noise, key: str, shift_x: DensityDescriptor, shift_z: DensityDescriptor) -> Density[dft.config_noise]:
    ""
    return Density(dft.config_noise(noise, key, shift_x, shift_z))