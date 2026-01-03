"""It is complicated ..."""

from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import Any, ClassVar, Literal, Self, Callable, Literal

from rhombus.core.additional_resource import AdditionalResource

__all__ = [
    "REGISTERED_DENSITY_FUNCTION_TYPES", "decode_HOLDER_HELPER_CODEC", "DensityFunctionType",
    "SimpleFunctionBase", "MappedFunctionBase", "DoubleArgumentFunctionBase", "MultiArgumentsFunctionBase"
]

#======// Main Decoding Function //==============================================================//

REGISTERED_DENSITY_FUNCTION_TYPES: set[type[DensityFunctionType]] = set()
"Set of all defined classes inheriting from `DensityFunctionTypeBase`."

def decode_HOLDER_HELPER_CODEC(o: dict | str | float, /) -> DensityFunctionType:
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

    REGISTRY = {t.id: t for t in REGISTERED_DENSITY_FUNCTION_TYPES if hasattr(t, "id")}
    if isinstance(o, dict):
        t: str = o.get("type")
        if t is None:
            raise ValueError("Cannot decode dict as HOLDER_HELPER_CODEC argument without key 'type'")
        if not ":" in t:
            t = "minecraft:" + t
        if REGISTRY.get(t) is None:
            raise TypeError(f"Cannot decode dict as HOLDER_HELPER_CODEC argument with type id '{t}'. No density function type class with adequate id is defined")
        return REGISTRY.get(t).decode(o)
    elif isinstance(o, (int, float)):
        return constant(float(o))
    elif isinstance(o, str):
        return Reference(o)
    else:
        raise TypeError(f"Cannot decode type '{type(o).__name__}' as HOLDER_HELPER_CODEC argument")


#======// Function Type Base Classes //==========================================================//

class DensityFunctionType:
    """Base class for density function types.
    """
    id: ClassVar[str]

    decode: ClassVar[Callable[[type[Self], dict], Self]]
    encode: ClassVar[Callable[[Self], dict]]
      
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        REGISTERED_DENSITY_FUNCTION_TYPES.add(cls)
    
@dataclass 
class SimpleFunctionBase(DensityFunctionType):#
    "Base class for density function types with no arguments."

    @classmethod
    def decode(cls, data: dict) -> Self:
        return cls()
    
    def encode(self) -> dict:
        return {"type": self.id}
    
@dataclass
class MappedFunctionBase(DensityFunctionType):
    "Base class for density function types that map an argument `argument` to a value."
    argument: DensityFunctionType

    @classmethod
    def decode(cls, data: dict) -> Self:
        argument = data["argument"]
        return cls(decode_HOLDER_HELPER_CODEC(argument))
    
    def encode(self) -> dict:
        return {"type": self.id, "argument": self.argument.encode()}

@dataclass()
class DoubleArgumentFunctionBase(DensityFunctionType):
    "Base class for density function types with two arguments `argument1` and `argument2`."
    argument1: DensityFunctionType
    argument2: DensityFunctionType

    @classmethod
    def decode(cls, data: dict) -> Self:
        argument1 = data["argument1"]
        argument2 = data["argument2"]
        return cls(
            decode_HOLDER_HELPER_CODEC(argument1),
            decode_HOLDER_HELPER_CODEC(argument2)
        )
    
    def encode(self) -> dict:
        return {"type": self.id, "argument1": self.argument1.encode(), "argument2": self.argument2.encode()}
    
class MultiArgumentsFunctionBase(DensityFunctionType):
    """Base class for density function types with any number of arguments of primitive types.

    When inheriting from this class, add the `@dataclass` decorator to the new class<br>
    and add fields with the same keys as required in the density function JSON definition.<br>
    """

    @classmethod
    def decode(cls, data: dict) -> Self:
        # fs = {f.name: f for f in fields(cls)}
        return cls(**{
            parameter: decode_HOLDER_HELPER_CODEC(value)# if fs[parameter].type is DensityFunctionType else value
            for parameter, value in data.items()
            if parameter in {f.name for f in fields(cls) if f.init}
        })

    def encode(self) -> dict:
        return {"type": self.id, **{
            parameter: value.encode() if isinstance(value, (DensityFunctionType, AdditionalResource)) else value
            for parameter, value
            in {f.name: getattr(self, f.name) for f in fields(self) if f.init}.items()
        }}


#======// Reference Classes //===================================================================//

@dataclass    
class Reference(DensityFunctionType):
    reference: str
    default: DensityFunctionType = field(init=True, default=None)
    
    @classmethod
    def decode(cls, data: str) -> Reference:
        return cls(data)
    
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
    input: DensityFunctionType
    min: float
    max:float

@dataclass
class constant(DensityFunctionType):
    id: ClassVar[str] = "minecraft:constant"
    argument: float

    @classmethod
    def decode(cls, data: dict | float) -> constant:
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
    density: DensityFunctionType
    upper_bound: DensityFunctionType
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
class noise(DensityFunctionType):
    id: ClassVar[str] = "minecraft:noise"
    noise: AdditionalResource
    xz_scale: float
    y_scale: float

    @classmethod
    def decode(cls, data: dict) -> noise:
        from rhombus.language.noise import Noise
        return cls(
            Noise(None, None, data["noise"]),
            data["xz_scale"],
            data["y_scale"],
        )

    def encode(self):
        return {
            "type": self.id,
            "noise": self.noise.reference_identifier,
            "xz_scale": self.xz_scale,
            "y_scale": self.y_scale,
        }

@dataclass
class old_blended_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:old_blended_noise"
    xz_scale: float
    y_scale: float
    xz_factor: float
    y_factor: float
    smear_scale_multiplier: float

class quarter_negative(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:quarter_negative"

@dataclass
class range_choice(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:range_choice"
    input: DensityFunctionType
    min_inclusive: float
    max_exclusive: float
    when_in_range: DensityFunctionType
    when_out_of_range: DensityFunctionType

@dataclass
class shift(DensityFunctionType):
    id: ClassVar[str] = "minecraft:shift"
    argument: AdditionalResource

    @classmethod
    def decode(cls, data: dict) -> shift:
        from rhombus.language.noise import Noise
        return cls(
            Noise(None, None, data["argument"])
        )

    def encode(self):
        return {
            "type": self.id,
            "argument": self.argument.reference_identifier,
        }

@dataclass
class shift_a(DensityFunctionType):
    id: ClassVar[str] = "minecraft:shift_a"
    argument: AdditionalResource

    @classmethod
    def decode(cls, data: dict) -> shift_a:
        from rhombus.language.noise import Noise
        return cls(
            Noise(None, None, data["argument"])
        )

    def encode(self):
        return {
            "type": self.id,
            "argument": self.argument.reference_identifier,
        }

@dataclass
class shift_b(DensityFunctionType):
    id: ClassVar[str] = "minecraft:shift_b"
    argument: AdditionalResource

    @classmethod
    def decode(cls, data: dict) -> shift_b:
        from rhombus.language.noise import Noise
        return cls(
            Noise(None, None, data["argument"])
        )

    def encode(self):
        return {
            "type": self.id,
            "argument": self.argument.reference_identifier,
        }

@dataclass
class shifted_noise(DensityFunctionType):
    id: ClassVar[str] = "minecraft:shifted_noise"
    noise: AdditionalResource
    xz_scale: float
    y_scale: float
    shift_x: DensityFunctionType
    shift_y: DensityFunctionType
    shift_z: DensityFunctionType

    @classmethod
    def decode(cls, data: dict) -> shifted_noise:
        from rhombus.language.noise import Noise
        return cls(Noise(None, None, data["noise"]), **{
            k: v
            for k, v
            in data.items()
            if k in {f.name for f in fields(cls) if f.init} and k not in ["type", "noise"]
        })

    def encode(self):
        return {
            "type": self.id,
            "noise": self.noise.reference_identifier,
            "xz_scale": self.xz_scale,
            "y_scale": self.y_scale,
            "shift_x": self.shift_x.encode(),
            "shift_y": self.shift_y.encode(),
            "shift_z": self.shift_z.encode(),
        }

class slide(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:slide"

@dataclass
class spline(DensityFunctionType):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: DensityFunctionType
    points: list[tuple[float, float | DensityFunctionType, float]]

    
    @classmethod
    def decode(cls, data: dict) -> spline:
        return cls(
            decode_HOLDER_HELPER_CODEC(data["spline"]["coordinate"]),
            [
                (point["location"], decode_HOLDER_HELPER_CODEC(point["value"]), point["derivative"])
                for point in data["spline"]["points"]
            ]
        )
    
    def encode(self) -> dict[str, Any]:
        return {
            "type": self.id,
            "spline": {
                "coordinate": self.coordinate.encode(),
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].encode() if isinstance(point[1], DensityFunctionType) else point[1],
                        "derivative": point[2], 
                    }
                    for point in self.points
                ]
            }
        }

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
    continentalness: DensityFunctionType
    erosion: DensityFunctionType
    weirdness: DensityFunctionType

@dataclass
class weird_scaled_sampler(DensityFunctionType):
    id: ClassVar[str] = "minecraft:weird_scaled_sampler"
    rarity_value_mapper: Literal["type_1", "type_2"]
    noise: AdditionalResource
    input: DensityFunctionType

    @classmethod
    def decode(cls, data: dict) -> weird_scaled_sampler:
        from rhombus.language.noise import Noise
        return cls(
            data["rarity_value_mapper"],
            Noise(None, None, data["noise"]),
            decode_HOLDER_HELPER_CODEC(data["input"])
        )

    def encode(self):
        return {
            "type": self.id,
            "rarity_value_mapper": self.rarity_value_mapper,
            "noise": self.noise.reference_identifier,
            "input": self.input.encode(),
        }

@dataclass
class y_clamped_gradient(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:y_clamped_gradient"
    from_y: int
    to_y: int
    from_value: float
    to_value: float