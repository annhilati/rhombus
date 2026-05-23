from typing import ClassVar, Self

from beet.contrib.worldgen import WorldgenDensityFunction

from rhombus.core.node import RhombusASTNode
from rhombus.core.serializer import deserialize_any_inline, serialize_any_inline
from rhombus.core.utils import JSONDict, BeetFile, annotated_fields
from rhombus import config

__all__ = [
    "DensityFunction",
    "SimpleFunctionBase", "MappedFunctionBase", "DoubleArgumentFunctionBase", "MultiArgumentsFunctionBase",
    "Reference", "constant"
]


#======// DensityFunction Base Class //==========================================================//

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
    
    def serialize_toplevel(self) -> JSONDict:
        return {"type": self.id, **{
            parameter: serialize_any_inline(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }}
        
    # serialize_inline() inherited from RhombusASTNode

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict | float | int) -> Self:
        
        if cls is DensityFunction:
            # Standard JSON object with 'type' key
            if isinstance(data, dict):
                type_field: str | None = data.get("type")
                if type_field is None:
                    raise ValueError("Cannot deserialize density function from dict without key 'type'")
                if ":" not in type_field:
                    type_field = "minecraft:" + type_field
                target_class = DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.get(type_field)
                if target_class is None:
                    raise TypeError(
                        f"Cannot deserialize density function with type id '{type_field}' from dict. "
                        "No density function class with this id is defined"
                    )
                    
                return target_class.deserialize_toplevel(data)
                    
            # Literal constant
            elif isinstance(data, (int, float)):
                return constant(float(data))

            else:
                raise TypeError(f"Cannot deserialize type '{type(data).__name__}' to density function at top level")
            
        fields = annotated_fields(cls)

        return cls(**{
            parameter: deserialize_any_inline(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })
                

    @classmethod
    def deserialize_inline(cls, data: JSONDict | float | int | str):
        # Literal reference
        if isinstance(data, str):
            return Reference.deserialize_inline(data)
        # Constant or dictionary
        elif isinstance(data, (dict, float, int)):
            return cls.deserialize_toplevel(data)
        else:
            raise TypeError(f"Cannot deserialize type '{type(data).__name__}' to density function inline")
        

#======// Utility Base Classes //================================================================//

class SimpleFunctionBase(DensityFunction):
    "Base class for density function types with no arguments."

    @classmethod
    def deserialize_toplevel(cls, data: dict = {}) -> Self:
        return cls()
    
    def serialize_toplevel(self) -> JSONDict:
        return {"type": self.id}
    
class MultiArgumentsFunctionBase(DensityFunction):
    """Base class for density function types with any number of arguments of primitive types.

    When inheriting from this class, add the `@dataclass` decorator to the new class  
    and add fields with the same keys as required in the density function JSON definition.

    If types are needed in the fields that are not of type `DensityFunction`,  
    of a subclass of `DatapackResource` or JSON-compatible, inherit from  
    `DensityFunction` instead and implement the methods manually.  
    """

class MappedFunctionBase(MultiArgumentsFunctionBase):
    "Base class for density function types that map an argument `argument` to a value."
    argument: DensityFunction
    
    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + self.argument.__repr__() + ")"

class DoubleArgumentFunctionBase(MultiArgumentsFunctionBase):
    "Base class for density function types with two arguments `argument1` and `argument2`."
    argument1: DensityFunction
    argument2: DensityFunction
    
    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + self.argument1.__repr__() + ", " + self.argument2.__repr__() + ")"

    
#======// Super Primitives //====================================================================//

class Reference(DensityFunction):
    reference: str
    definition: DensityFunction | None = None

    def __post_init__(self):
        if not isinstance(self.definition, DensityFunction) and self.definition is not None:
            raise ValueError(f"Cannot initialize Reference object with default of type {type(self.definition)}")
    
    @classmethod
    def deserialize_inline(cls, data: str):
        data = "minecraft:" + data if ":" not in data else data
       
        dp = config.ctx.datapack.get()
        if dp is not None and (f := dp[WorldgenDensityFunction].get(data)) is not None:
            return DensityFunction.deserialize_toplevel(f.data)
            
        return Reference(data, definition=None)
    
    # deserialize_toplevel() is not a realistic scenario
    
    def serialize_toplevel(self) -> JSONDict:
        from rhombus.std import vdft
        return vdft.add(self, vdft.constant(0.0)).serialize_toplevel()
    
    def serialize_inline(self) -> str:
        return self.reference
    
    def additional_described_files(self) -> dict[str, BeetFile]:
        files = {}
        if self.definition is not None:
            files[self.reference] = WorldgenDensityFunction(self.definition.serialize_toplevel())
            files |= self.definition.additional_described_files()
        return files
    
    def __repr__(self) -> str:
        if self.definition is None:
            return '"' + self.reference + '"'
        elif "generated" in self.reference:
            return "Density.partitioned(" + self.definition.__repr__() + ")"
        else:
            return "Density.configured(" + f"\"{self.reference}\"" + f", {self.definition.__repr__()}" + ")"
    
    
class constant(DensityFunction):
    id: ClassVar[str] = "minecraft:constant"
    argument: float
    
    @classmethod
    def deserialize_toplevel(cls, data: dict | int | float):
        if isinstance(data, dict):
            return cls(float(data["argument"]))    
        return cls(float(data))
            
    def serialize_toplevel(self) -> float | JSONDict:
        
        from rhombus.std import vdft
        
        def float_to_mul(value: float):

            if abs(value) < 65536.0 * 16:
                return value

            return vdft.mul(float_to_mul(value / 65536.0), 65536.0,).serialize_inline()
        
        return float_to_mul(self.argument)

    def __repr__(self) -> str:
        return str(self.argument)