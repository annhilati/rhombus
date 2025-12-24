"""It is complicated ..."""

from __future__ import annotations
from typing import Any, ClassVar, Literal, Self, TypeVar, Callable
from dataclasses import dataclass, fields, asdict

DFType = TypeVar("DFType", bound="DensityFunctionTypeBase")
"Type variable for all subclasses of `DensityFunctionTypeBase`."

REGISTERED_DENSITY_FUNCTION_TYPES: list[type[DFType]] = []
"List of all defined classes inheriting from `DensityFunctionTypeBase`."

def decode_HOLDER_HELPER_CODEC(o: dict | float | str) -> DFType:
    "Decodes any JSON value that can be used as a HOLDER_HELPER_CODEC type argument in a density function."
    REGISTRY = {t.id: t for t in REGISTERED_DENSITY_FUNCTION_TYPES}
    if isinstance(o, dict):
        t: str = o.get("type")
        if not ":" in t:
            t = "minecraft:" + t
        if t is None:
            raise ValueError("Cannot decode dict as HOLDER_HELPER_CODEC without key 'type'")
        if REGISTRY.get(t) is None:
            raise TypeError(f"Cannot decode dict as HOLDER_HELPER_CODEC with type id '{t}' because no DensityFunctionType with id adequate id is defined")
        return REGISTRY.get(t).decode(o)
    elif isinstance(o, (int, float)):
        return constant(float(o))
    elif isinstance(o, str):
        return Reference(o)
    else:
        raise TypeError(f"Cannot decode type '{type(o).__name__}' as HOLDER_HELPER_CODEC")



#======// Function Type Base Classes //==========================================================//

class DensityFunctionTypeBase:
    """Base class for density function types.
    
    To add new types, create a sublass and set a ClassVar `id` or override the `as_dict` method."""
    id: str

    encode: ClassVar[Callable[[Self], dict]]
    decode: ClassVar[Callable[[type[Self], dict], Self]]
    
    @property
    def params(self):
        return {f.name: getattr(self, f.name) for f in fields(self)}
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        REGISTERED_DENSITY_FUNCTION_TYPES.append(cls)
    
    def __repr__(self):
        return f"{type(self).__name__}({", ".join([f'{key}={value}' for key, value in self.params.items()])})"

@dataclass 
class MakeFunctionBase(DensityFunctionTypeBase):

    @classmethod
    def decode(cls, data: dict) -> Self:
        return cls()
    
    def encode(self) -> dict:
        return {"type": self.id}
    
@dataclass
class MappedFunctionBase(DensityFunctionTypeBase):
    argument: DFType

    @classmethod
    def decode(cls, data: dict) -> Self:
        argument = data["argument"]
        return cls(decode_HOLDER_HELPER_CODEC(argument))
    
    def encode(self) -> dict:
        return {"type": self.id, "argument": self.argument}

@dataclass
class DoubleArgumentFunctionBase(DensityFunctionTypeBase):
    argument1: DFType
    argument2: DFType

    @classmethod
    def decode(cls, data: dict) -> Self:
        argument1 = data["argument1"]
        argument2 = data["argument2"]
        return cls(
            decode_HOLDER_HELPER_CODEC(argument1),
            decode_HOLDER_HELPER_CODEC(argument2)
        )
    
    def encode(self) -> dict:
        return {"type": self.id, "argument1": self.argument1, "argument2": self.argument2}
    
class ManyArgumentsFunctionBase(DensityFunctionTypeBase):
    """Only inherit from this class, when the parameters in JSON-format are the same in the class.<br>
    When inheriting from this class, don't forget to add the @dataclass decorator, because the init has to be generated from the parameters.
    """

    @classmethod
    def decode(cls, data: dict) -> Self:
        fs = {f.name: f for f in fields(cls)}
        cls(**{
            parameter: decode_HOLDER_HELPER_CODEC(value) if fs[parameter].type is DFType else value
            for parameter, value in data.items()
            if parameter in {f.name for f in fields(cls) if f.init}
        })

    def encode(self) -> dict:
        fs = {f.name: f for f in fields(self)}
        return {"type": self.id, **{
            parameter: value.as_dict() if getattr(value, "as_dict") else value
            for parameter, value
            in asdict(self).items()
            if fs[parameter].init
        }}


#======// Function Type Classes //===============================================================//

@dataclass    
class Reference(DensityFunctionTypeBase):
    identifier: str
    
    def encode(self) -> str:
        return self.identifier
    
    @classmethod
    def decode(cls, data: str) -> Reference:
        return cls(data)

class abs(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:abs" 

class add(DoubleArgumentFunctionBase): 
    id: ClassVar[str] = "minecraft:add"

class beardifier(MakeFunctionBase):
    id: ClassVar[str] = "minecraft:beardifier"

class blend_alpha(MakeFunctionBase):
    id: ClassVar[str] = "minecraft:blend_alpha"

class blend_density(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:blend_density"

class blend_offset(MakeFunctionBase):
    id: ClassVar[str] = "minecraft:blend_offset"

class cache_2d(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_2d"

class cache_all_in_cell(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_all_in_cell"

class cache_once(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_once"

@dataclass
class clamp(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:clamp"
    input: DFType
    min: float
    max:float

@dataclass
class constant(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:constant"
    argument: float

    def encode(self) -> float:
        return self.argument
    
    @classmethod
    def decode(cls, data: dict | float) -> constant:
        return cls(data["argument"] if isinstance(data, dict) else data)

class cube(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cube"

class end_islands(MakeFunctionBase):
    id: ClassVar[str] = "minecraft:end_islands"

@dataclass
class find_top_surface(ManyArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:find_top_surface"
    density: DFType
    upper_bound: DFType
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
class noise(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:noise"
    noise: Any
    xz_scale: float
    y_scale: float

    @classmethod
    def decode(cls, data: dict) -> noise:
        from density.noise import Noise
        return cls(
            Noise(None, None, data["noise"]),
            data["xz_scale"],
            data["y_scale"],
        )

    def encode(self):
        if self.noise.reference is None:
            raise NotImplementedError
        return {
            "type": self.id,
            "noise": self.noise.reference,
            "xz_scale": self.xz_scale,
            "y_scale": self.y_scale,
        }

@dataclass
class old_blended_noise(ManyArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:old_blended_noise"
    xz_scale: float
    y_scale: float
    xz_factor: float
    y_factor: float
    smear_scale_multiplier: float

class quarter_negative(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:quarter_negative"

@dataclass
class range_choice(ManyArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:range_choice"
    input: DFType
    min_inclusive: float
    max_exclusive: float
    when_in_range: DFType
    when_out_of_range: DFType

@dataclass
class shift(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:shift"
    argument: Any

    @classmethod
    def decode(cls, data: dict) -> shift:
        from density.noise import Noise
        return cls(
            Noise(None, None, data["argument"])
        )

    def encode(self):
        if self.argument.reference is None:
            raise NotImplementedError
        return {
            "type": self.id,
            "argument": self.argument.reference,
        }

@dataclass
class shift_a(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:shift_a"
    argument: Any

    @classmethod
    def decode(cls, data: dict) -> shift_a:
        from density.noise import Noise
        return cls(
            Noise(None, None, data["argument"])
        )

    def encode(self):
        if self.argument.reference is None:
            raise NotImplementedError
        return {
            "type": self.id,
            "argument": self.argument.reference,
        }

@dataclass
class shift_b(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:shift_b"
    argument: Any

    @classmethod
    def decode(cls, data: dict) -> shift_b:
        from density.noise import Noise
        return cls(
            Noise(None, None, data["argument"])
        )

    def encode(self):
        if self.argument.reference is None:
            raise NotImplementedError
        return {
            "type": self.id,
            "argument": self.argument.reference,
        }

@dataclass
class shifted_noise(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:shifted_noise"
    noise: Any
    xz_scale: float
    y_scale: float
    shift_x: DFType
    shift_y: DFType
    shift_z: DFType

    def encode(self):
        if self.noise.reference is None:
            raise NotImplementedError
        return {
            "type": self.id,
            "noise": self.noise.reference,
            "xz_scale": self.xz_scale,
            "y_scale": self.y_scale,
            "shift_x": self.shift_x.as_dict() if getattr(self.shift_x, "as_dict") else self.shift_x,
            "shift_y": self.shift_y.as_dict() if getattr(self.shift_y, "as_dict") else self.shift_y,
            "shift_z": self.shift_z.as_dict() if getattr(self.shift_z, "as_dict") else self.shift_z,
        }
    
    @classmethod
    def decode(cls, data: dict) -> shifted_noise:
        from density.noise import Noise
        return cls(Noise(None, None, data["noise"]), **{
            k: v
            for k, v
            in data.items()
            if k in {f.name for f in fields(cls) if f.init} and k not in ["type", "noise"]
        })

class slide(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:slide"

@dataclass
class spline(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: DFType
    points: list[tuple[float, float | DFType, float]]

    def encode(self) -> dict[str, Any]:
        return {
            "type": self.id,
            "spline": {
                "coordinate": self.coordinate,
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].as_dict() if getattr(point[1], "as_dict") else point[1],
                        "derivative": point[2], 
                    }
                    for point in self.points
                ]
            }
        }
    
    @classmethod
    def decode(cls, data: dict) -> spline:
        return cls(
            decode_HOLDER_HELPER_CODEC(data["spline"]["coordinate"]),
            [
                (point["location"], decode_HOLDER_HELPER_CODEC(point["value"]), point["derivative"])
                for point in data["spline"]["points"]
            ]
        )

class square(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:square"

class squeeze(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:squeeze"

@dataclass
class terrain_shaper_spline(ManyArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:terrain_shaper_spline"
    spline: Literal["offset", "factor", "jaggedness"]
    min_value: float
    max_value: float
    continentalness: DFType
    erosion: DFType
    weirdness: DFType

@dataclass
class weird_scaled_sampler(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:weird_scaled_sampler"
    rarity_value_mapper: Literal["type_1", "type_2"]
    noise: Any
    input: DFType

    @classmethod
    def decode(cls, data: dict) -> weird_scaled_sampler:
        from density.noise import Noise
        return cls(
            data["rarity_value_mapper"],
            Noise(None, None, data["noise"]),
            decode_HOLDER_HELPER_CODEC(data["input"])
        )

    def encode(self):
        if self.noise.reference is None:
            raise NotImplementedError
        return {
            "type": self.id,
            "rarity_value_mapper": self.rarity_value_mapper,
            "noise": self.noise.reference,
            "input": self.input.as_dict() if getattr(self.input, "as_dict", None) else self.input,
        }

@dataclass
class y_clamped_gradient(ManyArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:y_clamped_gradient"
    from_y: int
    to_y: int
    from_value: float
    to_value: float