"""[Tectonic](https://modrinth.com/datapack/tectonic) by Apollo"""

from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from rhombus.core.df_types import MappedFunctionBase, MultiArgumentsFunctionBase, DensityFunctionType, decode_HOLDER_HELPER_CODEC
from rhombus.core.additional_resource import AdditionalResource
from rhombus.language.density import Density, DensityDescriptor, coerce_density_ASTs
from rhombus.language.noise import Noise

__all__ = ["invert", "config_constant", "config_noise"]

class df_types:

    class invert(MappedFunctionBase):
        id: ClassVar[str] = "tectonic:invert"

    @dataclass
    class config_constant(MultiArgumentsFunctionBase):
        id: ClassVar[str] = "tectonic:config_constant"
        key: str

    @dataclass
    class config_noise(DensityFunctionType):
        id: ClassVar[str] = "minecraft:noise"
        noise: AdditionalResource
        key: str
        shift_x: DensityFunctionType
        shift_z: DensityFunctionType

        @classmethod
        def decode(cls, data: dict) -> df_types.config_noise:
            return cls(
                Noise(None, None, data["noise"]),
                data["key"],
                decode_HOLDER_HELPER_CODEC(data["shift_x"]),
                decode_HOLDER_HELPER_CODEC(data["shift_y"]),
            )

        def encode(self):
            return {
                "type": self.id,
                "noise": self.noise.reference_identifier,
                "key": self.key,
                "xz_scale": self.shift_x.encode(),
                "y_scale": self.shift_z.encode(),
            }

@coerce_density_ASTs
def invert(argument: DensityDescriptor) -> Density[df_types.invert]:
    """Calculates `1/x`.
    """
    return Density(df_types.invert(argument))

def config_constant(key: str) -> Density[df_types.config_constant]:
    "References a constant from the Tectonic configuration."
    return Density(df_types.config_constant(key))

@coerce_density_ASTs
def config_noise(noise: Noise, key: str, shift_x: DensityDescriptor, shift_z: DensityDescriptor) -> Density[df_types.config_noise]:
    ""
    return Density(df_types.config_noise(noise, key, shift_x, shift_z))