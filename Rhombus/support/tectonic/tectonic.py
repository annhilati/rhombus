from dataclasses import dataclass
from typing import ClassVar
from Rhombus.core.density_function import MappedFunctionBase, MultiArgumentsFunctionBase, DensityFunction, decode_HOLDER_HELPER_CODEC
from Rhombus.core.registry_resource import RegistryResource
from Rhombus.core.noise import Noise
from Rhombus.language.density import Density, DensityDescriptor, BuiltinWizard

class dft:

    class invert(MappedFunctionBase):
        id: ClassVar[str] = "tectonic:invert"

    @dataclass
    class config_constant(MultiArgumentsFunctionBase):
        id: ClassVar[str] = "tectonic:config_constant"
        key: str

    @dataclass
    class config_noise(MultiArgumentsFunctionBase):
        id: ClassVar[str] = "minecraft:noise"
        noise: RegistryResource
        key: str
        shift_x: DensityFunction
        shift_z: DensityFunction


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