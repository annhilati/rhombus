from typing import ClassVar, Self, Any, Iterable
from types import ModuleType
import warnings

from beet.contrib.worldgen import WorldgenDensityFunction

from rhombus.core.node import RhombusASTNode
from rhombus.core.serializer import deserialize_any_inline, serialize_any_inline
from rhombus.core.utils import JSONDict, BeetFile, annotated_fields
from rhombus import config

__all__ = [
    "DensityFunction",
    "SimpleFunctionBase", "MappedFunctionBase", "DoubleArgumentFunctionBase",
    "Reference", "constant",
    "register"
]


def register(*add: type["DensityFunction"] | ModuleType | Any, rm: Iterable[str | type["DensityFunction"]] = []) -> dict[str, tuple[str, type["DensityFunction"]]]:
    """Registers or removes `DensityFunction` type subclasses from the deserialization register.
    
    Parameters:
        *add (type[DensityFunction] | module | Any): Objects to register density function types from.
            If it is not a `DensityFunction` subclass, its attributes will be searched for
            such. If it is a module, the serach is recursive.
        rm (str | type[DensityFunction]): Density function types to remove from the deserialization register.

    Returns:
        The deserialization register after registration. Maps density function
            type identifiers to tuples of the selected `DensityFunction` classes'
            module paths and type objects.
    """
    registrations = {}

    def try_register(o: Any):
        if isinstance(o, type) and issubclass(o, DensityFunction):
            if hasattr(o, "id") and isinstance(o.id, str):
                registrations[o.id] = o
        else:
            if hasattr(o, "__dict__"):
                for attribute in o.__dict__.values():
                    try_register(attribute)

    for o in add:
        if isinstance(o, type) and issubclass(o, DensityFunction):
            if not hasattr(o, "id") or not isinstance(o.id, str):
                raise ValueError(f"Cannot register density function type '{o.__name__}' without class variable 'id' defined")
            
        try_register(o)

    DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES |= registrations

    for rem in rm:
        if isinstance(rem, str):
            keys_to_remove = [k for k in DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES if k == rem or (":" not in rem and k == f"minecraft:{rem}")]
            for k in keys_to_remove:
                DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.pop(k, None)
        elif isinstance(rem, type):
            keys_to_remove = [k for k, v in DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.items() if v is rem]
            for k in keys_to_remove:
                DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.pop(k, None)

    if add and not registrations:
        warnings.warn("No DensityFunction subclasses were found to register from the given objects", UserWarning)

    return {id: (f"{typ.__module__}.{typ.__qualname__}", typ) for id, typ in sorted(DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.items())}
        

#======// DensityFunction Base Class //==========================================================//

class DensityFunction(RhombusASTNode):
    """Base class for density function types with any number of arguments of primitive types.

    When inheriting from this class, add fields with the same names as keys required in the
    density function JSON definition.

    If types are needed in the fields that are not of type `DensityFunction`, of a subclass
    of `DatapackResource` or otherwise JSON-compatible (like literals and `SubParameter`
    subclasses), implement the serialization methods manually.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/density_functions/)
    """
    fileclass: ClassVar[type[BeetFile]] = WorldgenDensityFunction
    id: ClassVar[str]
    
    REGISTERED_DENSITY_FUNCTION_TYPES: ClassVar[dict[str, type["DensityFunction"]]] = {}
    "Dict of all defined classes inheriting from `DensityFunction` with their ids as the keys."
              
    
    #======// Serialization //===================================================================//
    
    def serialize_toplevel(self) -> JSONDict:
        return {"type": self.id, **{
            parameter: serialize_any_inline(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }}
        
    # serialize_inline() is inherited from RhombusASTNode

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict | float | int) -> Self:
        
        if cls is DensityFunction:
            # Standard JSON object with 'type' key
            if isinstance(data, dict):
                
                type_field: str | None = data.get("type")
                
                if type_field is None:
                    raise ValueError("Cannot deserialize density function from dictionary without key 'type'")
                if ":" not in type_field:
                    type_field = "minecraft:" + type_field
                
                target_class = DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.get(type_field)
                if target_class is None:
                    raise TypeError(
                        f"Cannot deserialize density function with type '{type_field}' from dictionary. "
                        "No DensityFunction subclass with this id is defined"
                    )
                    
                return target_class.deserialize_toplevel(data)
                    
            # Literal constant
            elif isinstance(data, (int, float)):
                return constant(float(data))

            else:
                raise TypeError(f"Cannot deserialize density function from type '{data.__class__.__name__}' at top level")
            
        fields = annotated_fields(cls)

        return cls(**{
            parameter: deserialize_any_inline(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })
                

    @classmethod
    def deserialize_inline(cls, data: JSONDict | float | int | str) -> Self:
        # Literal reference
        if isinstance(data, str):
            return Reference.deserialize_inline(data)
        # Constant or dictionary
        elif isinstance(data, (dict, float, int)):
            return cls.deserialize_toplevel(data)
        else:
            raise TypeError(f"Cannot deserialize inline density function from type '{data.__class__.__name__}'")
        

#======// Utility Base Classes //================================================================//

class SimpleFunctionBase(DensityFunction):
    "Base class for density function types with no arguments."

    @classmethod
    def deserialize_toplevel(cls, data: dict = {}) -> Self:
        return cls()
    
    def serialize_toplevel(self) -> JSONDict:
        return {"type": self.id}
    
class MappedFunctionBase(DensityFunction):
    "Base class for density function types that map an argument `argument` to a value."
    argument: DensityFunction
    
    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + self.argument.__repr__() + ")"

class DoubleArgumentFunctionBase(DensityFunction):
    "Base class for density function types with two arguments `argument1` and `argument2`."
    argument1: DensityFunction
    argument2: DensityFunction
    
    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + self.argument1.__repr__() + ", " + self.argument2.__repr__() + ")"

    
#======// Primitives //==========================================================================//

class Reference(DensityFunction):
    reference: str
    definition: DensityFunction | None = None

    def __post_init__(self):
        if not isinstance(self.reference, str) or not self.reference:
            raise ValueError("Reference must have a reference of type str defined")
        if self.definition is not None and not isinstance(self.definition, DensityFunction):
            raise ValueError(f"Cannot initialize Reference object with default of type {self.definition.__class__.__name__}")
    
    @classmethod
    def deserialize_inline(cls, data: str):
        data = "minecraft:" + data if ":" not in data else data
       
        dp = config.ctx.datapack.get()
        if dp is not None and (f := dp[WorldgenDensityFunction].get(data)) is not None:
            return Reference(data, DensityFunction.deserialize_toplevel(f.data)) # TODO: Make it an option whether to return content or defined reference?
            
        return Reference(data)
    
    # deserialize_toplevel() is not a realistic scenario
    
    def serialize_toplevel(self) -> JSONDict:
        from rhombus.std import types
        return types.add(self, constant(0.0)).serialize_toplevel()
    
    def serialize_inline(self) -> str:
        return self.reference
    
    @property
    def inscribed_toplevel_nodes(self) -> set[RhombusASTNode]:
        nodes = set()
        if self.definition is not None:
            nodes.add(self)
            nodes |= self.definition.inscribed_toplevel_nodes
        return nodes
    
    def __repr__(self) -> str:
        from rhombus.std import types
        if self.definition is None:
            return '"' + self.reference + '"'
        elif "generated" in self.reference: # TODO: this should not be hardcoded
            types_with_implicit_partitioning = (types.cache_2d, types.cache_once, types.flat_cache, types.cache_all_in_cell) # TODO: this should not be hardcoded
            if isinstance(self.definition, types_with_implicit_partitioning):
                return self.definition.__repr__()
            return "Density.partitioned(" + self.definition.__repr__() + ")" 
        else:
            return "Density.configured(\"" + self.reference + f"\", {self.definition.__repr__()}" + ")"
    
    
class constant(DensityFunction):
    id: ClassVar[str] = "minecraft:constant"
    argument: float
    
    @classmethod
    def deserialize_toplevel(cls, data: dict | int | float):
        if isinstance(data, dict):
            return cls(float(data["argument"]))    
        return cls(float(data))
            
    def serialize_toplevel(self) -> float | JSONDict:
        from rhombus.std import types
        
        def float_to_mul(value: float):

            if abs(value) < 65536.0 * 16:
                return value

            return types.mul(float_to_mul(value / 65536.0), 65536.0,).serialize_inline()
        
        return float_to_mul(self.argument)

    def __repr__(self) -> str:
        return str(self.argument)