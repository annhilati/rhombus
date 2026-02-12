from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar, Optional

from beet.contrib.worldgen import WorldgenNoise
from Rhombus.core.additional_resource import AdditionalResource
from Rhombus.core.utils import JSONDict, uuid_hash

@dataclass(frozen=True)
class Noise(AdditionalResource):
    """Defines a perlin noise.

    **NOTE** To add a reference to an existing noise, use `ReferenceNoise()` instead.
    
    ### firstOctave
    `firstOctave` controls the base frequency of the noise. More negative values lead to more vast regions.<br>
    The scale in blocks over which the noise changes significantly is approximately `2^(-firstOctave)`.<br>
    E.g.: `-9` corresponds to ~512 blocks between two oppositely polarized areas.

    ### amplitudes
    The amplitudes control how detailed the noise is.<br>
    Every amplitude adds an overlayed copy ("octave") of the noise half the scale of the octave before.<br>
    The magnitude of the amplitudes are relative weight factors. A `0` skips the octave.

    Fractal like amplitudes like `[1.0, 0.5, 0.25]` are considered especially natural.

    [Minecraft Wiki Reference](https://minecraft.wiki/w/Noise)
    """
 
    fileclass: ClassVar = WorldgenNoise

    firstOctave: int           = field(init=True)
    amplitudes:  list[float]   = field(init=True)
    reference:   Optional[str] = field(init=True, default=None)
    "When given, the Noise object is a reference to an externally declared noise."

    def __post_init__(self):
        if self.reference is None and (self.firstOctave is None or self.amplitudes is None):
            raise ValueError("Noise must either have fields 'firstOctave' and 'amplitudes' or reference an externally provided noise")
        

    #======// Methods required by AdditionalResourceBase //================================//
    
    @property
    def reference_identifier(self) -> str:
        if self.reference is not None:
            return self.reference if ":" in self.reference else "minecraft:" + self.reference
        return f"rhombus:generated/" + uuid_hash(self.encode())

    @classmethod
    def decode(cls, data: JSONDict) -> Noise:
        cls(firstOctave=data["firstoctave"], amplitudes=data["amplitudes"])

    def encode(self) -> JSONDict:
        if self.firstOctave is None or self.amplitudes is None:
            raise Exception
        return {
            "firstOctave": self.firstOctave,
            "amplitudes": self.amplitudes
        }
       
    def __eq__(self, other: Noise):
        if not isinstance(other, Noise):
            return None
        if self.reference is None and other.reference is None:
            return (self.firstOctave == other.firstOctave) and (self.amplitudes == other.amplitudes)
        return self.reference == other.reference


@dataclass(init=False)
class ReferenceNoise:
    """Returns a Noise with a reference to an externally provided noise.
    """

    def __new__(identifier: str, /) -> Noise:
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier
        return Noise(firstOctave=None, amplitudes=None, reference=identifier)