__all__ = ["SubParameters"]


from typing import Self, ClassVar

from rhombus.core.utils import JSONDict, annotated_fields
from rhombus.core.node import RhombusASTNode
from rhombus.core.serializer import deserialize_any_inline, serialize_any_inline


class SubParameters(RhombusASTNode):
    """The **`SubParameters`** base class implements functionality for nodes
    in the abstract syntax tree of Rhombus that simply represent a grouping
    of parameters. This is a concept very similar to Pythons `TypedDict` class.

    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/devs/abstraction/)
    """

    fileclass: ClassVar[None] = None

    # ======// Serialization //===================================================================//

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> Self:
        from rhombus.core.environment import rho
        fields = annotated_fields(cls)
        rhombus_fields = getattr(cls, "__rhombus_fields__", {})

        kwargs = {}
        for parameter, tp in fields.items():
            meta = rhombus_fields.get(parameter)
            json_key = parameter
            if meta:
                json_key = meta.get_appropriate_key(rho, default=parameter)
            
            found_key = None
            if json_key in data:
                found_key = json_key
            elif meta and meta.legacy_keys:
                for legacy_key in meta.legacy_keys.values():
                    if legacy_key in data:
                        found_key = legacy_key
                        break
            
            if found_key:
                val = deserialize_any_inline(data[found_key], tp)
                if meta and meta.validate and val is not None and not meta.validate(val):
                    raise ValueError(f"Validation failed for field '{parameter}' of '{cls.__name__}'")
                kwargs[parameter] = val
                
        return cls(**kwargs)

    def serialize_toplevel(self) -> JSONDict:
        from rhombus.core.environment import rho
        result = {}
        rhombus_fields = getattr(self.__class__, "__rhombus_fields__", {})
        
        for parameter, value in self.fields.items():
            if value is None:
                continue
            
            meta = rhombus_fields.get(parameter)
            json_key = parameter
            if meta:
                json_key = meta.get_appropriate_key(rho, default=parameter)
                if meta.validate and not meta.validate(value):
                    raise ValueError(f"Validation failed for field '{parameter}' of '{self.__class__.__name__}'")
            
            result[json_key] = serialize_any_inline(value)
            
        return result
