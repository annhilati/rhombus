from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar, Optional
from beet.contrib.worldgen import WorldgenNoise
from Rhombus.core.registry_resource import RegistryResource
from Rhombus.core.utils import JSONDict

@dataclass(frozen=True)
class Noise(RegistryResource):
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

    firstOctave: int
    amplitudes:  list[float]
    reference:   Optional[str] = None

    def __post_init__(self):
        if self.reference is None and (self.firstOctave is None or self.amplitudes is None):
            raise ValueError("Noise must either have fields 'firstOctave' and 'amplitudes' or reference an externally provided noise")
        

    #======// Methods required by RegistryResourceBase //================================//
     
    @classmethod
    def referenced(cls, id: str):
        id = "minecraft:" + id if not ":" in id else id
        return cls(firstOctave=None, amplitudes=None, reference=id)

    @classmethod
    def decode(cls, data: JSONDict) -> Noise:
        return cls(firstOctave=data["firstOctave"], amplitudes=data["amplitudes"])

    def encode(self) -> JSONDict:
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