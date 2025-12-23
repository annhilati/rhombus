from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class Noise():
    """Declares a perlin noise.

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
 
    firstOctave: int         | None
    amplitudes:  list[float] | None
    reference:   str         | None
    "When given, the Noise object is a reference to an externally declared noise."

    def as_file(self) -> dict[str: Any]:
        if self.firstOctave is None or self.amplitudes is None:
            raise Exception
        return {
            "firstOctave": self.firstOctave,
            "amplitudes": self.amplitudes
        }

    def __eq__(self, other: Noise):
        if self.reference is None and other.reference is None:
            return (self.firstOctave == other.firstOctave) and (self.amplitudes == other.amplitudes)
        return self.reference == other.reference
    
    def __hash__(self):
        return hash(self.firstOctave) + hash(self.amplitudes)
    
def NoiseReference(identifier: str, /) -> Noise:
    "Returns a Noise with a reference to an external noise, defined somewhere in `worldgen/noise`."
    return Noise(None, None, identifier)