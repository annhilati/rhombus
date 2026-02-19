"""It is complicated ..."""

from dataclasses import dataclass, fields
from typing import Any, ClassVar, Self, Callable, get_type_hints, get_origin, get_args
from Rhombus import config
from Rhombus.core.registry_resource import RegistryResource, decode_RegistryResource_from_DataPack
from Rhombus.core.params import SubParameters
from Rhombus.core.utils import JSONDict, with_datapack_context, FROM_CONTEXT
import warnings, beet, beet.contrib.worldgen as beet_worldgen

__all__ = [
    "decode_HOLDER_HELPER_CODEC", "DensityFunction",
    "SimpleFunctionBase", "MappedFunctionBase", "DoubleArgumentFunctionBase", "MultiArgumentsFunctionBase",
    "Reference", "constant"
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

        default = None
        if dp is not None and (f := dp[beet_worldgen.WorldgenDensityFunction].get(o, default=None)) is not None:
            default = f.data
        out = Reference(o, default=decode_HOLDER_HELPER_CODEC(default) if default is not None else None)

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

    REGISTERED_DENSITY_FUNCTION_TYPES: ClassVar[dict[str, type["DensityFunction"]]] = {}
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
    
class MultiArgumentsFunctionBase(DensityFunction):
    """Base class for density function types with any number of arguments of primitive types.

    When inheriting from this class, add the `@dataclass` decorator to the new class<br>
    and add fields with the same keys as required in the density function JSON definition.<br>

    If types are needed in the fields that are not of type `DensityFunction`, of a subclass of `RegistryResource` or JSON-compatible, inherit from `DensityFunction` instead and implement the methods manually.
    """

    @classmethod
    def decode(cls, data: JSONDict) -> Self:
        init_fields: dict[str, type] = {
            f.name: get_type_hints(cls)[f.name]
            for f in fields(cls)
            if f.init
        }

        return cls(**{
            parameter: (
                decode_HOLDER_HELPER_CODEC(value)                   # DensityFunction
                    if tp is DensityFunction else
                decode_RegistryResource_from_DataPack(value, tp)    # Noise, ... (subclasses of RegistryResource)
                    if issubclass(tp, RegistryResource) else
                [decode_HOLDER_HELPER_CODEC(f) for f in value]      # list[DensityFunction]
                    if get_origin(tp) is list and get_args(tp)[0] is DensityFunction else
                tp.decode(value)                                    # (subclasses of SubParameters)
                    if issubclass(tp, SubParameters)

                else value
            )
            for parameter, value in data.items()
            if parameter in init_fields
            for tp in (init_fields[parameter],)
        })

    def encode(self) -> JSONDict:
        return {"type": self.id, **{
            parameter: (
                value.encode()                                      # DensityFunction
                    if isinstance(value, DensityFunction) else
                value.reference_identifier                          # Noise, ... (subclasses of RegistryResource)
                    if isinstance(value, RegistryResource) else
                [f.encode() for f in value]                         # list[DensityFunction]
                    if isinstance(value, list) and isinstance(value[0], (DensityFunction, None)) else
                value.encode()                                      # (subclasses of SubParameters)
                    if isinstance(value, SubParameters)

                else value)
            for parameter, value
            in self.fields.items()
        }}

@dataclass
class MappedFunctionBase(MultiArgumentsFunctionBase):
    "Base class for density function types that map an argument `argument` to a value."
    argument: DensityFunction

@dataclass
class DoubleArgumentFunctionBase(MultiArgumentsFunctionBase):
    "Base class for density function types with two arguments `argument1` and `argument2`."
    argument1: DensityFunction
    argument2: DensityFunction

    
#======// Reference Classes //===================================================================//

@dataclass    
class Reference(DensityFunction):
    reference: str
    default: DensityFunction | None = None
    
    @classmethod
    def decode(cls, data: str) -> "Reference":
        return decode_HOLDER_HELPER_CODEC(data)
    
    def encode(self) -> str:
        return self.reference
    
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
    def decode(cls, data: JSONDict | float) -> "constant":
        return cls(data["argument"] if isinstance(data, dict) else data)
    
    def encode(self) -> float:
        return self.argument