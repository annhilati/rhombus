from typing import Self

from rhombus.core.utils import JSONDict, annotated_fields
from rhombus.core.node import RhombusASTNode
from rhombus.core.serializer import deserialize_any_inline, serialize_any_inline

__all__ = ["SubParameters"]

class SubParameters(RhombusASTNode):
    """Base class for parameter groups that are used inline in fields of density function types or another.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/sub_parameters/)
    """
      
    #======// Serialization //===================================================================//
      
    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> Self:        
        fields = annotated_fields(cls)

        return cls(**{
            parameter: deserialize_any_inline(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })
    
    def serialize_toplevel(self) -> JSONDict:
        return {
            parameter: serialize_any_inline(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }