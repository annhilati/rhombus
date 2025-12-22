from dataclasses import dataclass, field
from typing import Any

@dataclass
class Noise():
    """Declares a perlin noise.
    
    firsOctave
    -----------
    `firstOctave` controls the base frequency of the noise. More negative values lead to more vast regions.<br>
    The scale in blocks over which the noise changes significantly is approximately `2^(-firstOctave)`.<br>
    E.g.: `-9` corresponds to ~512 blocks between two oppositely polarized areas.

    amplitudes
    -----------
    The amplitudes control how detailed the noise is.<br>
    Every amplitude adds an overlayed copy ("octave") of the noise half the size of the octave before.<br>
    The magnitude of the amplitudes are relative weight factors. A `0` skips the octave.

    Fractal like amplitudes like `[1.0, 0.5, 0.25]` are considered especially natural.

    [Minecraft Wiki Reference](https://minecraft.wiki/w/Noise)
    """
 
    reference:   str         | None = field(init=False, default=None)
    firstOctave: int
    amplitudes:  list[float]

    def as_file(self) -> dict[str: Any]:
        if self.firstOctave is None or self.amplitudes is None:
            raise Exception
        return {
            "firstOctave": self.firstOctave,
            "amplitudes": self.amplitudes
        }
    
def NoiseReference(identifier: str, /) -> Noise:
    "Returns a Noise with a reference to an external noise, defined somewhere in `worldgen/noise`."
    n = Noise(None, None)
    n.reference = identifier
    return n