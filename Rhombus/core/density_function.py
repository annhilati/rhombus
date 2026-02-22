"""It is complicated ..."""

from dataclasses import dataclass
from typing import Any, ClassVar, Self, Callable, get_origin, get_args
from Rhombus.core.registry_resource import DatapackResource
from Rhombus.core.utils import JSONDict, annotated_fields, fields

__all__ = [
    "DensityFunction",
    "SimpleFunctionBase", "MappedFunctionBase", "DoubleArgumentFunctionBase", "MultiArgumentsFunctionBase",
    "Reference", "constant"
]

#======// Main Decoding Function //==============================================================//



#======// Function Type Base Classes //==========================================================//

class DensityFunction:
    """Base class for density function types."""
    id: ClassVar[str]

    decode: ClassVar[Callable[[type[Self], JSONDict], Self]]
    encode: ClassVar[Callable[[Self], JSONDict | float | str]]
    # validate: ClassVar[Callable[[Self], None]]

    REGISTERED_DENSITY_FUNCTION_TYPES: ClassVar[dict[str, type["DensityFunction"]]] = {}
    "Set of all defined classes inheriting from `DensityFunctionTypeBase`."
      
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "id"):
            DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES[cls.id] = cls

    @property
    def fields(self) -> dict[str, Any]:
        "Returns the fields of the density function type with their values."
        return fields(self)

    
@dataclass
class SimpleFunctionBase(DensityFunction):
    "Base class for density function types with no arguments."

    @classmethod
    def decode(cls, data: dict = {}) -> Self:
        return cls()
    
    def encode(self) -> JSONDict:
        return {"type": self.id}
    
class MultiArgumentsFunctionBase(DensityFunction):
    """Base class for density function types with any number of arguments of primitive types.

    When inheriting from this class, add the `@dataclass` decorator to the new class<br>
    and add fields with the same keys as required in the density function JSON definition.<br>

    If types are needed in the fields that are not of type `DensityFunction`, of a subclass of `DatapackResource` or JSON-compatible, inherit from `DensityFunction` instead and implement the methods manually.
    """

    @classmethod
    def decode(cls, data: JSONDict) -> Self:
        from Rhombus.core.codec import decode_HOLDER_HELPER_CODEC, decode_DatapackResource_reference, decode as unidecode
        fields = annotated_fields(cls)

        return cls(**{
            parameter: (
                # DensityFunction
                decode_HOLDER_HELPER_CODEC(value)                   if tp is DensityFunction else
                # Noise, ... (subclasses of DatapackResource)
                decode_DatapackResource_reference(value, tp)    if issubclass(tp, DatapackResource) else
                # list[DensityFunction]
                [decode_HOLDER_HELPER_CODEC(f) for f in value]      if get_origin(tp) is list and get_args(tp)[0] is DensityFunction

                else unidecode(value, tp)
            )
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })

    def encode(self) -> JSONDict:
        from Rhombus.core.codec import encode as uniencode
        return {"type": self.id, **{
            parameter: uniencode(value)
            for parameter, value
            in self.fields.items()
            if value is not None
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
        from Rhombus.core.codec import decode_HOLDER_HELPER_CODEC
        return decode_HOLDER_HELPER_CODEC(data)
    
    def encode(self) -> str:
        return self.reference
    
@dataclass
class constant(DensityFunction):
    id: ClassVar[str] = "minecraft:constant"
    argument: float
            
    @classmethod
    def decode(cls, data: JSONDict | float) -> "constant":
        return cls(data["argument"] if isinstance(data, dict) else data)
    
    def encode(self) -> float:
        return self.argument