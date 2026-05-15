from dataclasses import dataclass
from typing import Any, ClassVar, Self
from rhombus.core.utils import JSONDict, annotated_fields, fields, BeetFileClass
from rhombus.core.node import Node, SerializationContext
from beet.contrib.worldgen import WorldgenDensityFunction

__all__ = [
    "DensityFunction",
    "SimpleFunctionBase", "MappedFunctionBase", "DoubleArgumentFunctionBase", "MultiArgumentsFunctionBase",
    "Reference", "constant"
]


#======// Function Type Base Classes //==========================================================//

class DensityFunction(Node):
    """Base class for density function types, which are the nodes of the density AST.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/density_functions/)
    """
    id: ClassVar[str]
    
    #======// Serialization //===================================================================//

    @classmethod
    def deserialize(cls, data: JSONDict) -> "DensityFunction":
        raise NotImplementedError
    
    def serialize(self) -> JSONDict | float | str:
        raise NotImplementedError
    
    REGISTERED_DENSITY_FUNCTION_TYPES: ClassVar[dict[str, type["DensityFunction"]]] = {}
    "Dict of all defined classes inheriting from `DensityFunction` with their ids as the keys."
      
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "id"):
            DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES[cls.id] = cls
        

@dataclass
class SimpleFunctionBase(DensityFunction):
    "Base class for density function types with no arguments."

    @classmethod
    def deserialize(cls, data: dict = {}) -> Self:
        return cls()
    
    def serialize(self) -> JSONDict:
        return {"type": self.id}
    
class MultiArgumentsFunctionBase(DensityFunction):
    """Base class for density function types with any number of arguments of primitive types.

    When inheriting from this class, add the `@dataclass` decorator to the new class  
    and add fields with the same keys as required in the density function JSON definition.

    If types are needed in the fields that are not of type `DensityFunction`,  
    of a subclass of `DatapackResource` or JSON-compatible, inherit from  
    `DensityFunction` instead and implement the methods manually.  
    """

    @classmethod
    def deserialize(cls, data: JSONDict) -> Self:
        from rhombus.core.serializer import deserialize
        fields = annotated_fields(cls)

        return cls(**{
            parameter: deserialize(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })

    def serialize(self) -> JSONDict:
        from rhombus.core.serializer import serialize
        return {"type": self.id, **{
            parameter: serialize(value)
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
    definition: DensityFunction | None = None

    def __post_init__(self):
        if not isinstance(self.definition, DensityFunction) and self.definition is not None:
            raise ValueError(f"Cannot initialize Reference object with default of type {type(self.definition)}")
    
    @classmethod
    def deserialize(cls, data: str) -> "Reference":
        from rhombus.core.serializer import decode_HOLDER_HELPER_CODEC
        return decode_HOLDER_HELPER_CODEC(data)
    
    def serialize(self) -> str:
        return self.reference
    
    def generated_files(self) -> dict[str, BeetFileClass]:
        files = {}
        if self.definition is not None:
            files[self.reference] = WorldgenDensityFunction(self.definition.serialize())
            files |= self.definition.generated_files()
        return files
    
    def __repr__(self) -> str:
        return self.reference
    
@dataclass
class constant(DensityFunction):
    id: ClassVar[str] = "minecraft:constant"
    argument: float
            
    @classmethod
    def deserialize(cls, data: JSONDict | float) -> "constant":
        return cls(data["argument"] if isinstance(data, dict) else data)
    
    def serialize(self) -> float:
        return self.argument

    def __repr__(self) -> str:
        return str(self.argument)