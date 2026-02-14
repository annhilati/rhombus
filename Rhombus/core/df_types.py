"""It is complicated ..."""

from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import Any, ClassVar, Literal, Self, Callable, Literal
from Rhombus.core.additional_resource import AdditionalResource, decode_additional_resource_from_datapack
from Rhombus.core.noise import Noise
from Rhombus.core import config, JSONDict
from Rhombus.core.utils import with_datapack_context, FROM_CONTEXT
import warnings, beet, beet.contrib.worldgen as beet_worldgen

__all__ = [
    "decode_HOLDER_HELPER_CODEC", "DensityFunction",
    "SimpleFunctionBase", "MappedFunctionBase", "DoubleArgumentFunctionBase", "MultiArgumentsFunctionBase"
]

#======// Main Decoding Function //==============================================================//

@with_datapack_context
def decode_HOLDER_HELPER_CODEC(o: dict | str | float, /, dp: beet.DataPack | None = FROM_CONTEXT) -> "DensityFunction":
    """Decodes any value that can be used as a HOLDER_HELPER_CODEC type argument in a density function.<br>
    (Either a JSON density function definiton, a string reference to another density function or a constant numeric value)

    Raises
    -------
    ValueError : When the dictionary has no key `'type'`
    TypeError : When no subclass of `DensityFunctionTypeBase` is defined, that has it's attribute `id` equal to `o["type"]` and thus, it is not known how to decode the dictionary
    """

    # `HOLDER_HELPER_CODEC` is a term used in the density function codebase for handling arguments,
    # that can either be a constant number, a reference to another density function, or a fully defined inline density function.<br>
    # There are other codecs for that too (see `clamp`), but for clarity and supportiveness we will only use this one.

    if isinstance(o, dict):
        t: str | None = o.get("type")
        if t is None:
            raise ValueError(
                "Cannot decode dict as HOLDER_HELPER_CODEC argument without key 'type'"
            )
        if ":" not in t:
            t = "minecraft:" + t
        cls = DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.get(t)
        if cls is None:
            raise TypeError(
                f"Cannot decode dict as HOLDER_HELPER_CODEC argument with type id '{t}'. "
                "No density function type class with adequate id is defined"
            )
        out = cls.decode(o)

    elif isinstance(o, (int, float)):
        out = constant(float(o))

    elif isinstance(o, str):
        o = "minecraft:" + o if ":" not in o else o

        if dp is not None and (f := dp[beet_worldgen.WorldgenDensityFunction].get(o, default=None)) is not None:
            default = f.data
        out = Reference(o, default=decode_HOLDER_HELPER_CODEC(default))

    else:
        raise TypeError(f"Cannot decode type '{type(o).__name__}' as HOLDER_HELPER_CODEC argument")

    return out


#======// Function Type Base Classes //==========================================================//

class DensityFunction:
    """Base class for density function types."""
    id: ClassVar[str]

    decode: ClassVar[Callable[[type[Self], JSONDict], Self]]
    encode: ClassVar[Callable[[Self], JSONDict | float | str]]
    validate: ClassVar[Callable[[Self], None]]

    REGISTERED_DENSITY_FUNCTION_TYPES: ClassVar[dict[str, type[DensityFunction]]] = {}
    "Set of all defined classes inheriting from `DensityFunctionTypeBase`."
      
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "id"):
            DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES[cls.id] = cls

    def __post_init__(self):
        if hasattr(self, "validate"):
            self.validate()

    @property
    def fields(self) -> dict[str, Any]:
        "Returns the fields of the density function type with their values."
        return {
            f.name: getattr(self, f.name, None)
            for f in fields(self)
            if f.init
        }
    
    @property
    def compilation_complexity(self) -> int:
        return 1 + sum([value.compilation_complexity for name, value in self.fields.items() if isinstance(value, DensityFunction)])

    
@dataclass
class SimpleFunctionBase(DensityFunction):
    "Base class for density function types with no arguments."

    @classmethod
    def decode(cls, data: dict) -> Self:
        return cls()
    
    def encode(self) -> JSONDict:
        return {"type": self.id}
    

@dataclass
class MappedFunctionBase(DensityFunction):
    "Base class for density function types that map an argument `argument` to a value."
    argument: DensityFunction

    @classmethod
    def decode(cls, data: JSONDict) -> Self:
        argument = data["argument"]
        return cls(decode_HOLDER_HELPER_CODEC(argument))
    
    def encode(self) -> JSONDict:
        return {"type": self.id, "argument": self.argument.encode()}


@dataclass
class DoubleArgumentFunctionBase(DensityFunction):
    "Base class for density function types with two arguments `argument1` and `argument2`."
    argument1: DensityFunction
    argument2: DensityFunction

    @classmethod
    def decode(cls, data: JSONDict) -> Self:
        return cls(
            decode_HOLDER_HELPER_CODEC(data["argument1"]),
            decode_HOLDER_HELPER_CODEC(data["argument2"])
        )
    
    def encode(self) -> JSONDict:
        return {"type": self.id, "argument1": self.argument1.encode(), "argument2": self.argument2.encode()}
    

class MultiArgumentsFunctionBase(DensityFunction):
    """Base class for density function types with any number of arguments of primitive types.

    When inheriting from this class, add the `@dataclass` decorator to the new class<br>
    and add fields with the same keys as required in the density function JSON definition.<br>

    If types are needed in the fields that are not `DensityFunctionType`, `AdditionalResource` or primitive, inherit from `DensityFunctionType` instead and implement the methods manually.
    """

    @classmethod
    def decode(cls, data: JSONDict) -> Self:
        init_fields = {
            f.name: f.type
            for f in fields(cls)
            if f.init
        }
        return cls(**{
            parameter: decode_HOLDER_HELPER_CODEC(value) if tp is DensityFunction else 
            decode_additional_resource_from_datapack(ref=value, t=tp) if isinstance(tp, AdditionalResource) else value
            for parameter, value in data.items()
            if parameter in init_fields
            for tp in (init_fields[parameter],)
        })

    def encode(self) -> JSONDict:
        return {"type": self.id, **{
            parameter: value.encode() if isinstance(value, DensityFunction) else value.reference_identifier if isinstance(value, AdditionalResource) else value
            for parameter, value
            in self.fields.items()
        }}


#======// Reference Classes //===================================================================//

@dataclass    
class Reference(DensityFunction):
    reference: str
    default: DensityFunction | None = field(init=True, default=None)
    
    @classmethod
    def decode(cls, data: str) -> Reference:
        return decode_HOLDER_HELPER_CODEC(data)
    
    def encode(self) -> str:
        return self.reference


#======// Function Type Classes //===============================================================//

class abs(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:abs" 

class add(DoubleArgumentFunctionBase): 
    id: ClassVar[str] = "minecraft:add"

class beardifier(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:beardifier"

class blend_alpha(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:blend_alpha"

class blend_density(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:blend_density"

class blend_offset(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:blend_offset"

class cache_2d(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_2d"

class cache_all_in_cell(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_all_in_cell"

class cache_once(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_once"

@dataclass
class clamp(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:clamp"
    input: DensityFunction
    min: float
    max:float

    def validate(self) -> None:
        if isinstance(self.input, Reference) and config.warn_on_reference_in_clamp:
            warnings.warn(
                "MC-252814: 'Clamp density function takes a direct input and doesn't allow a reference'.\n    "
                "An error might be thrown when loading a world.\n    "
                "For more information see https://bugs.mojang.com/browse/MC/issues/MC-252814"
            )

@dataclass
class constant(DensityFunction):
    id: ClassVar[str] = "minecraft:constant"
    argument: float

    def validate(self) -> None:
        limit = config.constant_number_limit
        if self.argument > limit or self.argument < -limit:
            warnings.warn(f"A constant with a value of {self.argument} lies outside the limit of ± {float(limit)}.\n    "
                          "An error might be thrown when loading a world.")

    @classmethod
    def decode(cls, data: JSONDict | float) -> constant:
        return cls(data["argument"] if isinstance(data, dict) else data)
    
    def encode(self) -> float:
        return self.argument

class cube(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cube"

class end_islands(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:end_islands"

@dataclass
class find_top_surface(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:find_top_surface"
    density: DensityFunction
    upper_bound: DensityFunction
    lower_bound: int
    cell_height: int

class flat_cache(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:flat_cache"

class half_negative(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:half_negative"

class interpolated(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:interpolated"

class invert(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:invert"

class max(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "minecraft:max"

class min(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "minecraft:min"

class mul(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "minecraft:mul"

@dataclass
class noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:noise"
    noise: Noise
    xz_scale: float
    y_scale: float

@dataclass
class old_blended_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:old_blended_noise"
    xz_scale: float
    y_scale: float
    xz_factor: float
    y_factor: float
    smear_scale_multiplier: float

    def validate(self) -> None:
        for param, value in {k: v for k, v in self.fields.items() if k != "smear_scale_multiplier"}.items():
            if value > 1000 or value < 0.001:
                warnings.warn(f"A value of {value} in the '{param}' field of 'old_blended_noise' lies outside the limit of 0.001 ≤ value ≤ 1000.0.\n    "
                              "An error might be thrown when loading a world.")
        if self.smear_scale_multiplier > 8 or self.smear_scale_multiplier < 1:
                warnings.warn(f"A value of {self.smear_scale_multiplier} in the 'smear_scale_multiplier' field of 'old_blended_noise' lies outside the limit of 1.0 ≤ value ≤ 8.0.\n    "
                              "An error might be thrown when loading a world.")


class quarter_negative(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:quarter_negative"

@dataclass
class range_choice(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:range_choice"
    input: DensityFunction
    min_inclusive: float
    max_exclusive: float
    when_in_range: DensityFunction
    when_out_of_range: DensityFunction

@dataclass
class shift(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:shift"
    argument: Noise

@dataclass
class shift_a(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:shift_a"
    argument: Noise

@dataclass
class shift_b(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:shift_b"
    argument: Noise

@dataclass
class shifted_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:shifted_noise"
    noise: Noise
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction

class slide(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:slide"

@dataclass
class spline(DensityFunction):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: DensityFunction
    points: list[tuple[float, DensityFunction, float]]

    @classmethod
    def decode(cls, data: JSONDict) -> spline:
        return cls(
            decode_HOLDER_HELPER_CODEC(data["spline"]["coordinate"]),
            [
                (point["location"], decode_HOLDER_HELPER_CODEC(point["value"]), point["derivative"])
                for point in data["spline"]["points"]
            ]
        )
    
    def encode(self) -> JSONDict:
        return {
            "type": self.id,
            "spline": {
                "coordinate": self.coordinate.encode(),
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].encode() if isinstance(point[1], DensityFunction) else point[1],
                        "derivative": point[2], 
                    }
                    for point in self.points
                ]
            }
        }
    
    @property
    def compilation_complexity(self) -> int:
        return 1 + self.coordinate.compilation_complexity + sum([p[1].compilation_complexity for p in self.points])

class square(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:square"

class squeeze(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:squeeze"

@dataclass
class terrain_shaper_spline(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:terrain_shaper_spline"
    spline: Literal["offset", "factor", "jaggedness"]
    min_value: float
    max_value: float
    continentalness: DensityFunction
    erosion: DensityFunction
    weirdness: DensityFunction

@dataclass
class weird_scaled_sampler(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:weird_scaled_sampler"
    rarity_value_mapper: Literal["type_1", "type_2"]
    noise: Noise
    input: DensityFunction

@dataclass
class y_clamped_gradient(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:y_clamped_gradient"
    from_y: int
    to_y: int
    from_value: float
    to_value: float

    def validate(self) -> None:
        if self.from_y > 4062 or self.from_y < -4064:
            warnings.warn(f"A value of {self.from_y} in the 'from_y' field of 'y_clamped_gradient' lies outside the limit of -4064 ≤ value ≤ 4062.\n    "
                          "An error might be thrown when loading a world.")
        if self.to_y > 4062 or self.to_y < -4064:
            warnings.warn(f"A value of {self.to_y} in the 'to_y' field of 'y_clamped_gradient' lies outside the limit of -4064 ≤ value ≤ 4062.\n    "
                          "An error might be thrown when loading a world.")
        if self.from_value > 4062 or self.from_value < -4064:
            warnings.warn(f"A value of {self.from_value} in the 'from_value' field of 'y_clamped_gradient' lies outside the limit of -1000000.0 ≤ value ≤ 1000000.0.\n    "
                          "An error might be thrown when loading a world.")
        if self.to_value > 4062 or self.to_value < -4064:
            warnings.warn(f"A value of {self.to_value} in the 'to_value' field of 'y_clamped_gradient' lies outside the limit of -1000000.0 ≤ value ≤ 1000000.0.\n    "
                          "An error might be thrown when loading a world.")