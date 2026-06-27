from typing import ClassVar, Literal

from rhombus.core.density_function import DensityFunction, MappedDensityFunction, SimpleDensityFunction
from rhombus.core.utils import JSONDict

from .fast_noise_config import FastNoiseConfig


#======// Density Function Classes //============================================================//

class axis(DensityFunction):
    id: ClassVar[str] = "lithostitched:axis"
    axis: Literal["x", "y", "z"]

class ceil(MappedDensityFunction):
    id: ClassVar[str] = "lithostitched:ceil"

class cos(MappedDensityFunction):
    id: ClassVar[str] = "lithostitched:cos"

class fast_noise(DensityFunction):
    id: ClassVar[str] = "lithostitched:fast_noise"
    config: FastNoiseConfig
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction

class floor(MappedDensityFunction):
    id: ClassVar[str] = "lithostitched:floor"

class mix(DensityFunction):
    id: ClassVar[str] = "lithostitched:mix"
    input: DensityFunction
    argument1: DensityFunction
    argument2: DensityFunction

class original_marker(SimpleDensityFunction):
    id: ClassVar[str] = "lithostitched:original_marker"

class select(DensityFunction):
    id: ClassVar[str] = "lithostitched:select"

    input: DensityFunction
    fallback: DensityFunction
    selections: list[tuple[float | tuple[float, float], DensityFunction]]

    @staticmethod
    def _deserialize_range(value: float | list[float]) -> float | tuple[float, float]:
        if isinstance(value, list):
            return (value[0], value[1])
        return value

    @staticmethod
    def _serialize_range(value: float | tuple[float, float]) -> float | list[float]:
        if isinstance(value, tuple):
            return [value[0], value[1]]

        return value

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> "select":
        return cls(
            DensityFunction.deserialize_inline(data["input"]),
            DensityFunction.deserialize_inline(data["fallback"]),
            [
                (
                    cls._deserialize_range(item["range"]),
                    DensityFunction.deserialize_inline(item["function"]),
                )
                for item in data["selections"]
            ],
        )

    def serialize_toplevel(self) -> JSONDict:
        return {
            "type": self.id,
            "select": {
                "input": self.input.serialize_inline(),
                "fallback": self.fallback.serialize_inline(),
                "selections": [
                    {
                        "range": self._serialize_range(rng),
                        "function": fn.serialize_inline(),
                    }
                    for rng, fn in self.selections
                ],
            },
        }
    
class shift(DensityFunction):
    id: ClassVar[str] = "lithostitched:shift"
    input: DensityFunction
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction

class sin(MappedDensityFunction):
    id: ClassVar[str] = "lithostitched:sin"

class sqrt(MappedDensityFunction):
    id: ClassVar[str] = "lithostitched:sqrt"

class wrapped_marker(SimpleDensityFunction):
    id: ClassVar[str] = "lithostitched:wrapped_marker"