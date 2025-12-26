from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, ClassVar, Optional
import base64, struct
from beet.contrib.worldgen import WorldgenNoise

from density.core.additional_resource import AdditionalResourceBase

@dataclass(frozen=True, repr=False)
class Noise(AdditionalResourceBase):
    """Defines a perlin noise.

    To add a reference to an existing noise, use `NoiseReference()` instead.
    
    ### firsOctave
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

    firstOctave: int           = field(init=True, default=None)
    amplitudes:  list[float]   = field(init=True, default=None)
    reference:   Optional[str] = field(init=True, default=None)
    "When given, the Noise object is a reference to an externally declared noise."

    def __post_innit__(self):
        if self.reference is None and (self.firstOctave is None or self.amplitudes is None):
            raise ValueError("Noise must have fields 'firstOctave' and 'amplitudes' or a reference.")

    @property    
    def identifier(self) -> str:
        if self.reference is not None:
            return self.reference
        
        data = struct.pack(">qI", self.firstOctave, len(self.amplitudes))
        for v in self.amplitudes:
            data += struct.pack(">d", float(v))
        return base64.b32encode(data).decode("ascii").rstrip("=")

    def encode(self) -> dict[str: Any]:
        if self.firstOctave is None or self.amplitudes is None:
            raise Exception
        return {
            "firstOctave": self.firstOctave,
            "amplitudes": self.amplitudes
        }
    
    @classmethod
    def decode(cls, data: dict) -> Noise:
        cls(firstOctave=data["firstoctave"], amplitudes=data["amplitudes"])

    @classmethod
    def from_encoded_string(cls, string: str) -> Noise:
        padding = "=" * (-len(string) % 8)
        data = base64.b32decode((string + padding).encode("ascii"))

        n, length = struct.unpack_from(">qI", data, 0)
        offset = struct.calcsize(">qI")

        values = list(struct.unpack_from(f">{length}d", data, offset))
        return cls(n, values)
    
    def __eq__(self, other: Noise):
        if self.reference is None and other.reference is None:
            return (self.firstOctave == other.firstOctave) and (self.amplitudes == other.amplitudes)
        return self.reference == other.reference
    
    def __hash__(self):
        return hash(self.firstOctave) + hash(self.amplitudes)
    
def NoiseReference(identifier: str, /) -> Noise:
    "Returns a Noise with a reference to an external noise, defined somewhere in `worldgen/noise`."
    return Noise(reference=identifier)