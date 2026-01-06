"""[Tectonic](https://modrinth.com/datapack/tectonic) by Apollo"""

from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from rhombus.core.df_types import MappedFunctionBase, MultiArgumentsFunctionBase, DensityFunctionType, decode_HOLDER_HELPER_CODEC
from rhombus.core.additional_resource import AdditionalResource
from rhombus.language.density import Density, unwrap_resolved
from rhombus.language.noise import Noise

__all__ = ["invert", "config_constant", "config_noise"]

class Invert(MappedFunctionBase):
    id: ClassVar[str] = "tectonic:invert"

@dataclass
class Config_constant(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "tectonic:config_constant"
    key: str

@dataclass
class Config_noise(DensityFunctionType):
    id: ClassVar[str] = "minecraft:noise"
    noise: AdditionalResource
    key: str
    shift_x: DensityFunctionType
    shift_z: DensityFunctionType

    @classmethod
    def decode(cls, data: dict) -> Config_noise:
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

def invert(argument: Density | str | float) -> Density[Invert]:
    """Calculates `1/x`.
    """
    argument, = unwrap_resolved(argument)
    return Density(Invert(argument))

def config_constant(key: str) -> Density[Config_constant]:
    "References a constant from the Tectonic configuration."
    return Density(Config_constant(key))

def config_noise(noise: Noise, key: str, shift_x: Density | str | float, shift_z: Density | str | float) -> Density[Config_noise]:
    ""
    shift_x, shift_z = unwrap_resolved(shift_x, shift_z)
    return Density(Config_noise(noise, key, shift_x, shift_z))