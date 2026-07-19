__all__ = [
    "slide",
    "terrain_shaper_spline",
    "weird_scaled_sampler",
]


from typing import ClassVar, Literal

from rhombus.core import DensityFunction, MappedDensityFunction, JSONDict
from rhombus.std import Noise


class slide(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:slide"


class spline(DensityFunction):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: DensityFunction
    points: list[tuple[float, DensityFunction, float]]
    min_value: float
    max_value: float

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> "spline":
        return cls(
            DensityFunction.deserialize_inline(data["spline"]["coordinate"]),
            [
                (
                    point["location"],
                    DensityFunction.deserialize_inline(
                        {"type": "minecraft:spline", "spline": point["value"]}
                    )
                    if isinstance(point["value"], dict)
                    and point["value"].get("type") is None
                    else DensityFunction.deserialize_inline(point["value"]),
                    point["derivative"],
                )
                for point in data["spline"]["points"]
            ],
            data["min_value"],
            data["max_value"],
        )

    def serialize_toplevel(self) -> JSONDict:
        return {
            "type": self.id,
            "spline": {
                "coordinate": self.coordinate.serialize_inline(),
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].serialize_inline()["spline"]
                        if isinstance(point[1].serialize_inline(), dict)
                        else point[1].serialize_inline(),
                        "derivative": point[2],
                    }
                    for point in self.points
                ],
            },
            "min_value": self.min_value,
            "max_value": self.max_value,
        }


class terrain_shaper_spline(DensityFunction):
    id: ClassVar[str] = "minecraft:terrain_shaper_spline"
    spline: Literal["offset", "factor", "jaggedness"]
    min_value: float
    max_value: float
    continentalness: DensityFunction
    erosion: DensityFunction
    weirdness: DensityFunction


class weird_scaled_sampler(DensityFunction):
    id: ClassVar[str] = "minecraft:weird_scaled_sampler"
    input: DensityFunction
    noise: Noise
    rarity_value_mapper: Literal["type_1", "type_2"]
