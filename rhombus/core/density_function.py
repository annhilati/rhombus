from dataclasses import dataclass
from typing import ClassVar, Self
from rhombus.core.utils import JSONDict, annotated_fields, BeetFile, FROM_CONTEXT, contextfunction
from rhombus.core.node import RhombusASTNode, SerializationContext
from beet.contrib.worldgen import WorldgenDensityFunction
import beet
from rhombus import config
from rhombus.core.serializer import deserialize, serialize

__all__ = [
    "DensityFunction",
    "SimpleFunctionBase", "MappedFunctionBase", "DoubleArgumentFunctionBase", "MultiArgumentsFunctionBase",
    "Reference", "constant"
]


#======// Function Type Base Classes //==========================================================//

class DensityFunction(RhombusASTNode):
    """Base class for density function types, which are the nodes of the density AST.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/density_functions/)
    """
    id: ClassVar[str]
    
    REGISTERED_DENSITY_FUNCTION_TYPES: ClassVar[dict[str, type["DensityFunction"]]] = {}
    "Dict of all defined classes inheriting from `DensityFunction` with their ids as the keys."
      
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "id"):
            DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES[cls.id] = cls
    
    #======// Serialization //===================================================================//

    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def deserialize(cls, data: JSONDict | str | float | int, ctx: SerializationContext, dp: beet.DataPack | None = FROM_CONTEXT) -> Self:
        fields = annotated_fields(cls)
        
        if isinstance(data, dict):
            t: str | None = data.get("type")
            if t is None:
                raise ValueError("Cannot deserialize density function from dict without key 'type'")
            if ":" not in t:
                t = "minecraft:" + t
            cls = DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.get(t)
            if cls is None:
                raise TypeError(
                    f"Cannot deserialize density function with type id '{t}' from dict. "
                    "No density function class with this id is defined"
                )
            
            return cls(**{
                parameter: deserialize(value, tp, SerializationContext.INLINE)
                for parameter, value in data.items()
                if parameter in fields
                for tp in (fields[parameter],)
            })
        
        elif isinstance(data, (int, float)):
            return constant(float(data))

        elif isinstance(data, str):
            data = "minecraft:" + data if ":" not in data else data

            default = None
            if dp is not None and (f := dp[WorldgenDensityFunction].get(data)) is not None:
                default = f.data
            return Reference(data, definition=deserialize(default, SerializationContext.TOPLEVEL) if default is not None else None)

        else:
            raise TypeError(f"Cannot decode type '{type(data).__name__}' as density function argument")

        
    def serialize(self, ctx: SerializationContext) -> JSONDict:
        
        return {"type": self.id, **{
            parameter: serialize(SerializationContext.INLINE)
            for parameter, value
            in self.fields.items()
            if value is not None
        }}
        

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
    
    # @classmethod
    # def deserialize(cls, data: str) -> "Reference":
    #     from rhombus.core.serializer import decode_HOLDER_HELPER_CODEC
    #     return decode_HOLDER_HELPER_CODEC(data)
    
    # def serialize(self) -> str:
    #     return self.reference
    
    def generated_files(self) -> dict[str, BeetFile]:
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
            
    # @classmethod
    # def deserialize(cls, data: JSONDict | float) -> "constant":
    #     return cls(data["argument"] if isinstance(data, dict) else data)
    
    # def serialize(self) -> float:
    #     return self.argument

    def __repr__(self) -> str:
        return str(self.argument)